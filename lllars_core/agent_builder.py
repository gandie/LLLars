from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from pydantic_ai import (
    Agent,
    InstrumentationSettings,
    ModelSettings,
    RunContext,
)
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

from lllars_core.config import HarnessConfig, ROOT, canonicalize_shell_command
from lllars_core.shell import run_powershell


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
) -> Agent:
    def _tool_error(
        tool_name: str,
        message: str,
        hint: str | None = None,
    ) -> str:
        clean = " ".join(message.strip().split())
        payload = f"[tool-error:{tool_name}] {clean}"
        if hint:
            payload = f"{payload} Hint: {hint}"
        emit_thought(payload)
        return payload

    model_obj = OllamaModel(
        parse_ollama_model(cfg.model),
        provider=OllamaProvider(
            base_url=normalize_ollama_base_url(cfg.provider_url)
        ),
    )

    agent = Agent(
        model_obj,
        instructions=f"{cfg.system_prompt}\n\n{cfg.tool_policy}",
        model_settings=ModelSettings(),
        retries={
            "tools": cfg.agent_retries_tools,
            "output": cfg.agent_retries_output,
        },
        tool_timeout=cfg.tool_timeout_sec,
        max_concurrency=cfg.max_concurrency,
        metadata={
            "harness": "lllars",
            "provider": "ollama",
            "project_root": str(cfg.project_root),
        },
    )

    if cfg.instrumentation_enabled:
        agent.instrument = InstrumentationSettings(
            include_content=cfg.instrumentation_include_content,
        )

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
            target = resolve_under(cfg.project_root, path)
            if not target.exists():
                return _tool_error(
                    "list_files",
                    f"Path not found: {path}",
                    "Choose an existing path under project_root.",
                )
            if target.is_file():
                return str(target.relative_to(cfg.project_root)).replace(
                    "\\", "/"
                )
            iterator = target.rglob("*") if recursive else target.iterdir()
            return "\n".join(
                sorted(
                    str(item.relative_to(cfg.project_root)).replace("\\", "/")
                    for item in iterator
                )
            )
        except Exception as exc:
            return _tool_error(
                "list_files",
                str(exc),
                "Only access files inside project_root.",
            )

    @agent.tool
    def read_file(ctx: RunContext[None], path: str) -> str:
        _ = ctx
        try:
            target = resolve_under(cfg.project_root, path)
            if not target.exists() or not target.is_file():
                return _tool_error(
                    "read_file",
                    f"File not found: {path}",
                    "Pass a valid file path under project_root.",
                )
            return target.read_text(encoding="utf-8")
        except Exception as exc:
            return _tool_error(
                "read_file",
                str(exc),
                "Only access files inside project_root.",
            )

    @agent.tool
    def write_file(ctx: RunContext[None], path: str, content: str) -> str:
        _ = ctx
        try:
            target = resolve_under(cfg.project_root, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            rel = str(target.relative_to(cfg.project_root)).replace("\\", "/")
            return f"Wrote {rel}"
        except Exception as exc:
            return _tool_error(
                "write_file",
                str(exc),
                "Use a writable path inside project_root.",
            )

    if cfg.allowed_shell_commands:

        @agent.tool
        def run_shell(
            ctx: RunContext[None],
            command: str,
            timeout_sec: int = 90,
        ) -> str:
            _ = ctx
            emit_thought("tool: run_shell")
            try:
                return _run_allowed_shell(command, timeout_sec)
            except Exception as exc:
                return _tool_error(
                    "run_shell",
                    str(exc),
                    "Use an allowlisted command and valid timeout.",
                )

    if cfg.test_command is not None:

        @agent.tool
        def run_test_command(ctx: RunContext[None]) -> str:
            _ = ctx
            emit_thought("tool: run_test_command")
            try:
                return _run_allowed_shell(cfg.test_command, 90)
            except Exception as exc:
                return _tool_error("run_test_command", str(exc))

    if cfg.eval_command is not None:

        @agent.tool
        def run_eval_command(ctx: RunContext[None]) -> str:
            _ = ctx
            emit_thought("tool: run_eval_command")
            try:
                return _run_allowed_shell(cfg.eval_command, 90)
            except Exception as exc:
                return _tool_error("run_eval_command", str(exc))

    return agent
