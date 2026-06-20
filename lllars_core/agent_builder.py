from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic_ai import Agent, ModelSettings, RunContext
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

from lllars_core.config import HarnessConfig, ROOT, canonicalize_shell_command
from lllars_core.shell import run_powershell


def default_runtime_telemetry() -> dict[str, Any]:
    return {
        "tool_calls_total": 0,
        "tool_calls_by_name": {},
        "tool_errors_total": 0,
        "tool_errors_by_name": {},
        "tool_error_samples": [],
        "tool_budget_exceeded": False,
        "tool_budget_exceeded_by_name": {},
        "tool_circuit_breaker_trips_total": 0,
        "tools_disabled_by_circuit_breaker": [],
        "read_calls": 0,
        "write_calls": 0,
        "list_calls": 0,
        "read_chars_total": 0,
        "write_chars_total": 0,
        "ollama_requests_estimated": 0,
        "ollama_responses_estimated": 0,
        "provider_response_ids_seen": 0,
    }


def resolve_under(root: Path, user_path: str) -> Path:
    candidate = Path(user_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError("Path is outside configured project-root")
    return candidate


def normalize_ollama_base_url(provider_url: str) -> str:
    base_url = provider_url.strip().rstrip("/")
    if not base_url:
        raise ValueError("Config is missing non-empty provider-url")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"
    return base_url


def parse_ollama_model(model_value: str) -> str:
    value = model_value.strip()
    if not value:
        raise ValueError("Config field model is empty")
    if value.startswith("ollama:"):
        return value.split(":", 1)[1]
    return value


def build_agent(
    cfg: HarnessConfig,
    emit_thought: Callable[[str], None],
    on_telemetry_update: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[Agent, dict[str, Any]]:
    model_obj = OllamaModel(
        parse_ollama_model(cfg.model),
        provider=OllamaProvider(base_url=normalize_ollama_base_url(cfg.provider_url)),
    )

    agent = Agent(
        model_obj,
        instructions=f"{cfg.system_prompt}\n\n{cfg.tool_policy}",
        model_settings=ModelSettings(),
    )

    telemetry = default_runtime_telemetry()
    tool_calls = {"count": 0, "by_name": {}}
    error_signatures: dict[tuple[str, str], int] = {}
    disabled_tools: dict[str, str] = {}

    def _flush() -> None:
        if on_telemetry_update is not None:
            on_telemetry_update(dict(telemetry))

    def _record_call(name: str) -> None:
        telemetry["tool_calls_total"] = int(telemetry["tool_calls_total"]) + 1
        by_name = telemetry["tool_calls_by_name"]
        if isinstance(by_name, dict):
            by_name[name] = int(by_name.get(name, 0)) + 1
        emit_thought(f"tool: {name}")
        _flush()

    def _record_error(name: str, message: str) -> str:
        telemetry["tool_errors_total"] = int(telemetry["tool_errors_total"]) + 1
        by_name = telemetry["tool_errors_by_name"]
        if isinstance(by_name, dict):
            by_name[name] = int(by_name.get(name, 0)) + 1
        samples = telemetry["tool_error_samples"]
        if isinstance(samples, list) and len(samples) < 5:
            samples.append(f"{name}: {message}")

        threshold = int(cfg.tool_error_circuit_breaker_threshold)
        if threshold > 0:
            signature = " ".join(message.strip().lower().split())
            key = (name, signature)
            next_count = int(error_signatures.get(key, 0)) + 1
            error_signatures[key] = next_count
            if next_count >= threshold and name not in disabled_tools:
                disabled_tools[name] = message
                telemetry["tool_circuit_breaker_trips_total"] = int(
                    telemetry["tool_circuit_breaker_trips_total"]
                ) + 1
                disabled = telemetry["tools_disabled_by_circuit_breaker"]
                if isinstance(disabled, list) and name not in disabled:
                    disabled.append(name)
                emit_thought(
                    f"circuit-breaker: disabled {name} after "
                    f"{next_count} repeated errors"
                )

        emit_thought(f"error in {name}: {message}")
        _flush()
        return f"[tool-error] {message}"

    def _ensure_enabled(name: str) -> None:
        if name in disabled_tools:
            raise RuntimeError(
                "Tool disabled by circuit breaker: "
                f"{name} ({disabled_tools[name]})"
            )

    def _consume_budget(name: str) -> None:
        tool_calls["count"] += 1
        by_name = tool_calls["by_name"]
        by_name[name] = int(by_name.get(name, 0)) + 1

        if tool_calls["count"] > cfg.tool_call_budget:
            telemetry["tool_budget_exceeded"] = True
            _flush()
            raise RuntimeError("Tool call budget exceeded")

        per_tool_limit = cfg.tool_call_budget_per_tool.get(name)
        if per_tool_limit is not None and by_name[name] > per_tool_limit:
            telemetry["tool_budget_exceeded"] = True
            budget_exceeded = telemetry["tool_budget_exceeded_by_name"]
            if isinstance(budget_exceeded, dict):
                budget_exceeded[name] = int(budget_exceeded.get(name, 0)) + 1
            _flush()
            raise RuntimeError(f"Tool call budget exceeded for {name}")

    def _guarded_start(name: str) -> None:
        _record_call(name)
        _ensure_enabled(name)
        _consume_budget(name)

    def _run_allowed_shell(command: str, timeout_sec: int) -> str:
        canonical = canonicalize_shell_command(command)
        if canonical not in cfg.allowed_shell_commands:
            payload = {
                "returncode": 126,
                "stdout": "",
                "stderr": "[lllars] rejected shell command: not in allowlist",
            }
            return json.dumps(payload)
        return json.dumps(
            run_powershell(command=command, cwd=ROOT, timeout_sec=timeout_sec)
        )

    @agent.tool
    def list_files(
        ctx: RunContext[None],
        path: str = ".",
        recursive: bool = True,
    ) -> str:
        _ = ctx
        try:
            _guarded_start("list_files")
            telemetry["list_calls"] = int(telemetry["list_calls"]) + 1
            target = resolve_under(cfg.project_root, path)
            if not target.exists():
                return _record_error("list_files", f"Path not found: {path}")
            if target.is_file():
                return str(target.relative_to(cfg.project_root)).replace("\\", "/")
            iterator = target.rglob("*") if recursive else target.iterdir()
            return "\n".join(
                sorted(
                    str(item.relative_to(cfg.project_root)).replace("\\", "/")
                    for item in iterator
                )
            )
        except Exception as exc:
            return _record_error("list_files", str(exc))

    @agent.tool
    def read_file(ctx: RunContext[None], path: str) -> str:
        _ = ctx
        try:
            _guarded_start("read_file")
            telemetry["read_calls"] = int(telemetry["read_calls"]) + 1
            target = resolve_under(cfg.project_root, path)
            if not target.exists() or not target.is_file():
                return _record_error("read_file", f"File not found: {path}")
            content = target.read_text(encoding="utf-8")
            trimmed = content[: cfg.file_read_char_limit]
            telemetry["read_chars_total"] = int(telemetry["read_chars_total"]) + len(
                trimmed
            )
            _flush()
            return trimmed
        except Exception as exc:
            return _record_error("read_file", str(exc))

    @agent.tool
    def write_file(ctx: RunContext[None], path: str, content: str) -> str:
        _ = ctx
        try:
            _guarded_start("write_file")
            telemetry["write_calls"] = int(telemetry["write_calls"]) + 1
            target = resolve_under(cfg.project_root, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            telemetry["write_chars_total"] = int(telemetry["write_chars_total"]) + len(
                content
            )
            _flush()
            rel = str(target.relative_to(cfg.project_root)).replace("\\", "/")
            return f"Wrote {rel}"
        except Exception as exc:
            return _record_error("write_file", str(exc))

    if cfg.allowed_shell_commands:

        @agent.tool
        def run_shell(
            ctx: RunContext[None],
            command: str,
            timeout_sec: int = 90,
        ) -> str:
            _ = ctx
            try:
                _guarded_start("run_shell")
                return _run_allowed_shell(command, timeout_sec)
            except Exception as exc:
                return _record_error("run_shell", str(exc))

    if cfg.test_command is not None:

        @agent.tool
        def run_test_command(ctx: RunContext[None]) -> str:
            _ = ctx
            try:
                _guarded_start("run_test_command")
                return _run_allowed_shell(cfg.test_command, 90)
            except Exception as exc:
                return _record_error("run_test_command", str(exc))

    if cfg.eval_command is not None:

        @agent.tool
        def run_eval_command(ctx: RunContext[None]) -> str:
            _ = ctx
            try:
                _guarded_start("run_eval_command")
                return _run_allowed_shell(cfg.eval_command, 90)
            except Exception as exc:
                return _record_error("run_eval_command", str(exc))

    return agent, telemetry
