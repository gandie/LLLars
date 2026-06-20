#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic_ai import Agent, ModelSettings, RunContext
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = ROOT / "lllars.example.json"
DEFAULT_TIMEOUT_SEC = 600
DEFAULT_TOOL_CALL_BUDGET = 24
DEFAULT_FILE_READ_CHAR_LIMIT = 20000


class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


@dataclass(frozen=True)
class HarnessConfig:
    model: str
    provider_url: str
    project_root: Path
    test_command: str
    eval_command: str | None
    eval_expect_json: bool
    eval_success_pass_rate: float
    allowed_shell_commands: set[str]
    system_prompt: str
    tool_policy: str
    tool_call_budget: int
    file_read_char_limit: int


def _canonicalize_shell_command(command: str) -> str:
    normalized = " ".join(command.strip().split())
    normalized = normalized.replace('"', "").replace("'", "")
    normalized = normalized.replace("\\", "/")
    return normalized


def _default_runtime_telemetry() -> dict[str, Any]:
    return {
        "tool_calls_total": 0,
        "tool_calls_by_name": {},
        "tool_errors_total": 0,
        "tool_errors_by_name": {},
        "tool_error_samples": [],
        "tool_budget_exceeded": False,
        "read_calls": 0,
        "write_calls": 0,
        "list_calls": 0,
        "read_chars_total": 0,
        "write_chars_total": 0,
        "ollama_requests_estimated": 0,
        "ollama_responses_estimated": 0,
        "provider_response_ids_seen": 0,
    }


def _truncate(value: str, max_len: int = 220) -> str:
    text = value.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _emit_live_thought(message: str) -> None:
    target = globals().get("_LLARS_THOUGHT_LOG_PATH")
    if not isinstance(target, Path):
        return
    try:
        with target.open("a", encoding="utf-8") as handle:
            handle.write(_truncate(message, 180) + "\n")
    except Exception:
        return


def _run_powershell(command: str, cwd: Path, timeout_sec: int) -> dict[str, Any]:
    p = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout_sec,
    )
    return {
        "returncode": p.returncode,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
    }


def _resolve_under(root: Path, user_path: str) -> Path:
    candidate = Path(user_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError("Path is outside configured project-root")
    return candidate


def _normalize_ollama_base_url(provider_url: str) -> str:
    base_url = provider_url.strip().rstrip("/")
    if not base_url:
        raise ValueError("Config is missing non-empty provider-url")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"
    return base_url


def _parse_ollama_model(model_value: str) -> str:
    value = model_value.strip()
    if not value:
        raise ValueError("Config field model is empty")
    if value.startswith("ollama:"):
        return value.split(":", 1)[1]
    return value


def _load_config(config_path: Path) -> HarnessConfig:
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError("Top-level config must be a JSON object")

    model = str(cfg.get("model", "")).strip()
    provider_url = str(cfg.get("provider-url", "")).strip()
    if not model or not provider_url:
        raise ValueError("Config requires model and provider-url")

    project_root_raw = str(cfg.get("project_root", "")).strip()
    if not project_root_raw:
        raise ValueError("Config requires project_root")
    project_root = (ROOT / project_root_raw).resolve()
    if not project_root.exists() or not project_root.is_dir():
        raise ValueError(f"Invalid project_root: {project_root}")

    commands = cfg.get("commands")
    if not isinstance(commands, dict):
        raise ValueError("Config requires commands object")

    test_command = str(commands.get("test", "")).strip()
    if not test_command:
        raise ValueError("Config requires commands.test")

    eval_command_raw = str(commands.get("eval", "")).strip()
    eval_command = eval_command_raw if eval_command_raw else None

    allowed_shell_commands = {_canonicalize_shell_command(test_command)}
    if eval_command:
        allowed_shell_commands.add(_canonicalize_shell_command(eval_command))

    extra = cfg.get("allowed_shell_commands", [])
    if isinstance(extra, list):
        for item in extra:
            text = str(item).strip()
            if text:
                allowed_shell_commands.add(_canonicalize_shell_command(text))

    system_prompt = str(cfg.get("system-prompt", "")).strip()
    if not system_prompt:
        system_prompt = "You are a coding agent."

    tool_policy = str(cfg.get("tool-policy", "")).strip()
    if not tool_policy:
        tool_policy = (
            "Tool policy:\n"
            "- Only edit files inside the project root.\n"
            "- Use list_files/read_file/write_file for file operations.\n"
            "- Use run_test_command for tests and run_eval_command for eval.\n"
            "- run_shell is restricted to the config allowlist.\n"
        )

    return HarnessConfig(
        model=model,
        provider_url=provider_url,
        project_root=project_root,
        test_command=test_command,
        eval_command=eval_command,
        eval_expect_json=bool(cfg.get("eval_expect_json", True)),
        eval_success_pass_rate=float(cfg.get("eval_success_pass_rate", 100.0)),
        allowed_shell_commands=allowed_shell_commands,
        system_prompt=system_prompt,
        tool_policy=tool_policy,
        tool_call_budget=int(cfg.get("tool_call_budget", DEFAULT_TOOL_CALL_BUDGET)),
        file_read_char_limit=int(cfg.get("file_read_char_limit", DEFAULT_FILE_READ_CHAR_LIMIT)),
    )


def _build_agent(
    cfg: HarnessConfig,
    on_telemetry_update: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[Agent, dict[str, Any]]:
    model_obj = OllamaModel(
        _parse_ollama_model(cfg.model),
        provider=OllamaProvider(base_url=_normalize_ollama_base_url(cfg.provider_url)),
    )

    agent = Agent(
        model_obj,
        instructions=f"{cfg.system_prompt}\n\n{cfg.tool_policy}",
        model_settings=ModelSettings(),
    )

    telemetry = _default_runtime_telemetry()
    tool_calls = {"count": 0}

    def _flush() -> None:
        if on_telemetry_update is not None:
            on_telemetry_update(dict(telemetry))

    def _record_call(name: str) -> None:
        telemetry["tool_calls_total"] = int(telemetry["tool_calls_total"]) + 1
        by_name = telemetry["tool_calls_by_name"]
        if isinstance(by_name, dict):
            by_name[name] = int(by_name.get(name, 0)) + 1
        _emit_live_thought(f"tool: {name}")
        _flush()

    def _record_error(name: str, message: str) -> str:
        telemetry["tool_errors_total"] = int(telemetry["tool_errors_total"]) + 1
        by_name = telemetry["tool_errors_by_name"]
        if isinstance(by_name, dict):
            by_name[name] = int(by_name.get(name, 0)) + 1
        samples = telemetry["tool_error_samples"]
        if isinstance(samples, list) and len(samples) < 5:
            samples.append(f"{name}: {message}")
        _emit_live_thought(f"error in {name}: {message}")
        _flush()
        return f"[tool-error] {message}"

    def _consume_budget() -> None:
        tool_calls["count"] += 1
        if tool_calls["count"] > cfg.tool_call_budget:
            telemetry["tool_budget_exceeded"] = True
            _flush()
            raise RuntimeError("Tool call budget exceeded")

    def _run_allowed_shell(command: str, timeout_sec: int) -> str:
        canonical = _canonicalize_shell_command(command)
        if canonical not in cfg.allowed_shell_commands:
            payload = {
                "returncode": 126,
                "stdout": "",
                "stderr": "[lllars] rejected shell command: not in allowlist",
            }
            return json.dumps(payload)
        return json.dumps(
            _run_powershell(command=command, cwd=ROOT, timeout_sec=timeout_sec)
        )

    @agent.tool
    def list_files(ctx: RunContext[None], path: str = ".", recursive: bool = True) -> str:
        _ = ctx
        try:
            _record_call("list_files")
            telemetry["list_calls"] = int(telemetry["list_calls"]) + 1
            _consume_budget()
            target = _resolve_under(cfg.project_root, path)
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
            _record_call("read_file")
            telemetry["read_calls"] = int(telemetry["read_calls"]) + 1
            _consume_budget()
            target = _resolve_under(cfg.project_root, path)
            if not target.exists() or not target.is_file():
                return _record_error("read_file", f"File not found: {path}")
            content = target.read_text(encoding="utf-8")
            trimmed = content[: cfg.file_read_char_limit]
            telemetry["read_chars_total"] = int(telemetry["read_chars_total"]) + len(trimmed)
            _flush()
            return trimmed
        except Exception as exc:
            return _record_error("read_file", str(exc))

    @agent.tool
    def write_file(ctx: RunContext[None], path: str, content: str) -> str:
        _ = ctx
        try:
            _record_call("write_file")
            telemetry["write_calls"] = int(telemetry["write_calls"]) + 1
            _consume_budget()
            target = _resolve_under(cfg.project_root, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            telemetry["write_chars_total"] = int(telemetry["write_chars_total"]) + len(content)
            _flush()
            rel = str(target.relative_to(cfg.project_root)).replace("\\", "/")
            return f"Wrote {rel}"
        except Exception as exc:
            return _record_error("write_file", str(exc))

    @agent.tool
    def run_shell(ctx: RunContext[None], command: str, timeout_sec: int = 90) -> str:
        _ = ctx
        _record_call("run_shell")
        _consume_budget()
        return _run_allowed_shell(command, timeout_sec)

    @agent.tool
    def run_test_command(ctx: RunContext[None]) -> str:
        _ = ctx
        _record_call("run_test_command")
        _consume_budget()
        return _run_allowed_shell(cfg.test_command, 90)

    @agent.tool
    def run_eval_command(ctx: RunContext[None]) -> str:
        _ = ctx
        _record_call("run_eval_command")
        _consume_budget()
        if cfg.eval_command is None:
            payload = {
                "returncode": 0,
                "stdout": "",
                "stderr": "eval not configured",
            }
            return json.dumps(payload)
        return _run_allowed_shell(cfg.eval_command, 90)

    return agent, telemetry


def _extract_thought_trace(result: Any) -> list[str]:
    trace: list[str] = []
    try:
        for msg in result.all_messages():
            if str(getattr(msg, "kind", "")) != "response":
                continue
            parts = getattr(msg, "parts", None)
            if not isinstance(parts, list):
                continue
            for part in parts:
                text = getattr(part, "content", None)
                if not isinstance(text, str) or not text.strip():
                    text = getattr(part, "text", None)
                if isinstance(text, str) and text.strip():
                    trace.append(_truncate(text, 180))
                tool_name = getattr(part, "tool_name", None)
                if isinstance(tool_name, str) and tool_name:
                    trace.append(f"tool-call: {tool_name}")
            if len(trace) >= 12:
                break
    except Exception:
        return []
    return trace[:12]


def _run_single_agent(cfg: HarnessConfig, prompt_text: str) -> dict[str, Any]:
    runtime_telemetry = _default_runtime_telemetry()

    def _persist(telemetry: dict[str, Any]) -> None:
        nonlocal runtime_telemetry
        runtime_telemetry = telemetry

    try:
        agent, runtime_telemetry = _build_agent(cfg, on_telemetry_update=_persist)
        _emit_live_thought("agent: started")
        result = agent.run_sync(prompt_text)
        _emit_live_thought("agent: completed")

        try:
            req = 0
            resp = 0
            response_ids = 0
            for msg in result.all_messages():
                kind = str(getattr(msg, "kind", ""))
                if kind == "request":
                    req += 1
                elif kind == "response":
                    resp += 1
                    if getattr(msg, "provider_response_id", None):
                        response_ids += 1
            runtime_telemetry["ollama_requests_estimated"] = req
            runtime_telemetry["ollama_responses_estimated"] = resp
            runtime_telemetry["provider_response_ids_seen"] = response_ids
        except Exception:
            pass

        return {
            "returncode": 0,
            "stdout": str(result.output),
            "stderr": "",
            "thought_trace": _extract_thought_trace(result),
            "runtime_telemetry": runtime_telemetry,
        }
    except Exception:
        return {
            "returncode": 125,
            "stdout": "",
            "stderr": traceback.format_exc(),
            "thought_trace": [],
            "runtime_telemetry": runtime_telemetry,
        }


def _run_agent_with_timeout(
    cfg: HarnessConfig,
    prompt_text: str,
    timeout_sec: int,
    show_progress: bool,
) -> tuple[str, str, int, dict[str, Any], list[str]]:
    payload_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        prefix="lllars_payload_",
        delete=False,
        encoding="utf-8",
    )
    payload_path = Path(payload_file.name)
    payload_file.close()

    prompt_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        prefix="lllars_prompt_",
        delete=False,
        encoding="utf-8",
    )
    prompt_path = Path(prompt_file.name)
    prompt_file.write(prompt_text)
    prompt_file.close()

    thought_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".log",
        prefix="lllars_thoughts_",
        delete=False,
        encoding="utf-8",
    )
    thought_path = Path(thought_file.name)
    thought_file.close()

    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--config",
        str(args_config_path()),
        "--internal-run",
        "--internal-prompt-file",
        str(prompt_path),
        "--internal-output-json",
        str(payload_path),
        "--internal-thought-log",
        str(thought_path),
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    start_time = time.time()
    thought_pos = 0
    latest_thought = ""
    last_render_width = 0
    spinner = ["|", "/", "-", "\\"]
    spin_idx = 0
    while proc.poll() is None:
        elapsed = int(time.time() - start_time)
        if thought_path.exists():
            try:
                with thought_path.open("r", encoding="utf-8", errors="replace") as handle:
                    handle.seek(thought_pos)
                    chunk = handle.read()
                    thought_pos = handle.tell()
                if chunk:
                    for line in chunk.splitlines():
                        stripped = line.strip()
                        if stripped:
                            latest_thought = _truncate(stripped, 90)
            except Exception:
                pass
        if elapsed > timeout_sec:
            proc.kill()
            proc.wait(timeout=5)
            payload_path.unlink(missing_ok=True)
            prompt_path.unlink(missing_ok=True)
            thought_path.unlink(missing_ok=True)
            if show_progress:
                print(
                    f"\r{Color.RED}[agent] timeout after {timeout_sec}s{Color.RESET}"
                    + " " * 20
                )
            return "", "[llars] agent timed out", 124, _default_runtime_telemetry(), []
        if show_progress:
            line = (
                f"{Color.CYAN}[agent] {spinner[spin_idx % 4]} "
                f"running {elapsed}s/{timeout_sec}s{Color.RESET}"
            )
            if latest_thought:
                line += f" {Color.YELLOW}| {latest_thought}{Color.RESET}"
            pad = " " * max(0, last_render_width - len(line))
            print(f"\r{line}{pad}", end="", flush=True)
            last_render_width = len(line)
            spin_idx += 1
        time.sleep(0.2)

    _, stderr_text = proc.communicate(timeout=5)
    if show_progress:
        elapsed_done = time.time() - start_time
        print(
            f"\r{Color.GREEN}[agent] done in {elapsed_done:.1f}s{Color.RESET}"
            + " " * 20
        )

    payload: dict[str, Any] = {
        "returncode": 125,
        "stdout": "",
        "stderr": stderr_text[-2000:],
        "runtime_telemetry": _default_runtime_telemetry(),
    }
    if payload_path.exists():
        try:
            loaded = json.loads(payload_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                payload = loaded
        except Exception:
            pass

    payload_path.unlink(missing_ok=True)
    prompt_path.unlink(missing_ok=True)
    thought_path.unlink(missing_ok=True)

    thought_trace = payload.get("thought_trace")
    if not isinstance(thought_trace, list):
        thought_trace = []

    return (
        str(payload.get("stdout", "")) or "",
        str(payload.get("stderr", "")) or "",
        int(payload.get("returncode", 125)),
        payload.get("runtime_telemetry")
        if isinstance(payload.get("runtime_telemetry"), dict)
        else _default_runtime_telemetry(),
        [str(item) for item in thought_trace],
    )


def _print_summary(result: dict[str, Any], verbose: bool) -> None:
    success = bool(result.get("success", False))
    status_text = "SUCCESS" if success else "FAILED"
    status_color = Color.GREEN if success else Color.RED

    elapsed = result.get("elapsed_sec", "?")
    agent_rc = int(result.get("agent_returncode", 125))
    test = result.get("test", {})
    test_rc = int(test.get("returncode", 1)) if isinstance(test, dict) else 1
    eval_json = result.get("eval")
    eval_error = result.get("eval_error")

    eval_text = "skipped"
    if isinstance(eval_json, dict):
        summary = eval_json.get("summary")
        if isinstance(summary, dict) and isinstance(summary.get("pass_rate"), (int, float)):
            eval_text = f"pass_rate={float(summary['pass_rate']):.1f}%"
        else:
            eval_text = "ok"
    elif isinstance(eval_error, str) and eval_error.strip():
        eval_text = f"error: {_truncate(eval_error, 90)}"

    print(f"{status_color}{Color.BOLD}{status_text}{Color.RESET}")
    print(f"time: {elapsed}s | agent_rc: {agent_rc} | test_rc: {test_rc} | eval: {eval_text}")

    if not success:
        stderr_preview = _truncate(str(result.get("agent_stderr", "")), 180)
        if stderr_preview:
            print(f"agent_error: {stderr_preview}")

    if not verbose:
        return

    print("\n-- verbose --")
    agent_stdout = str(result.get("agent_stdout", "")).strip()
    if agent_stdout:
        print("agent_output:")
        print(_truncate(agent_stdout, 1200))

    agent_stderr = str(result.get("agent_stderr", "")).strip()
    if agent_stderr:
        print("agent_stderr:")
        print(_truncate(agent_stderr, 1200))

    print("telemetry:")
    print(json.dumps(result.get("runtime_telemetry", {}), indent=2))

    print("raw_result:")
    print(json.dumps(result, indent=2))


def _run_eval(cfg: HarnessConfig) -> tuple[dict[str, Any] | None, str | None]:
    if cfg.eval_command is None:
        return None, None

    payload = _run_powershell(command=cfg.eval_command, cwd=ROOT, timeout_sec=120)
    if payload["returncode"] != 0:
        return None, payload["stderr"]

    if not cfg.eval_expect_json:
        return {
            "raw_stdout": payload["stdout"],
            "raw_stderr": payload["stderr"],
            "returncode": payload["returncode"],
        }, None

    try:
        parsed = json.loads(payload["stdout"])
    except Exception as exc:
        return None, str(exc)

    return parsed if isinstance(parsed, dict) else None, None


def _run_tests(cfg: HarnessConfig) -> dict[str, Any]:
    return _run_powershell(command=cfg.test_command, cwd=ROOT, timeout_sec=120)


def _is_eval_success(cfg: HarnessConfig, eval_json: dict[str, Any] | None) -> bool:
    if cfg.eval_command is None:
        return True
    if not isinstance(eval_json, dict):
        return False
    summary = eval_json.get("summary")
    if not isinstance(summary, dict):
        return False
    pass_rate = summary.get("pass_rate")
    if not isinstance(pass_rate, (int, float)):
        return False
    return float(pass_rate) >= cfg.eval_success_pass_rate


def args_config_path() -> Path:
    value = globals().get("_LLARS_CONFIG_PATH")
    if isinstance(value, Path):
        return value
    return DEFAULT_CONFIG_PATH


def main() -> None:
    ap = argparse.ArgumentParser(description="LLLARS single-shot runner")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    ap.add_argument("--prompt", help="Prompt text to run")
    ap.add_argument("--prompt-file", help="Path to prompt text file")
    ap.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--internal-run", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--internal-prompt-file", default="", help=argparse.SUPPRESS)
    ap.add_argument("--internal-output-json", default="", help=argparse.SUPPRESS)
    ap.add_argument("--internal-thought-log", default="", help=argparse.SUPPRESS)
    args = ap.parse_args()

    config_path = Path(args.config).resolve()
    globals()["_LLARS_CONFIG_PATH"] = config_path
    cfg = _load_config(config_path)

    if args.internal_run:
        if not args.internal_prompt_file or not args.internal_output_json:
            raise SystemExit(125)
        if args.internal_thought_log:
            globals()["_LLARS_THOUGHT_LOG_PATH"] = Path(args.internal_thought_log)
        prompt_text = Path(args.internal_prompt_file).read_text(encoding="utf-8")
        payload = _run_single_agent(cfg, prompt_text)
        Path(args.internal_output_json).write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        raise SystemExit(int(payload.get("returncode", 125)))

    if args.prompt:
        prompt_text = args.prompt
    elif args.prompt_file:
        prompt_text = Path(args.prompt_file).read_text(encoding="utf-8")
    else:
        raise SystemExit("Provide --prompt or --prompt-file")

    start = time.time()
    (
        agent_stdout,
        agent_stderr,
        agent_rc,
        telemetry,
        thought_trace,
    ) = _run_agent_with_timeout(
        cfg=cfg,
        prompt_text=prompt_text,
        timeout_sec=args.timeout_sec,
        show_progress=not args.internal_run,
    )
    elapsed = round(time.time() - start, 2)

    print(f"{Color.CYAN}[checks] running tests...{Color.RESET}")
    test_info = _run_tests(cfg)
    if cfg.eval_command:
        print(f"{Color.CYAN}[checks] running eval...{Color.RESET}")
    eval_json, eval_error = _run_eval(cfg)

    success = (
        agent_rc == 0
        and int(test_info.get("returncode", 1)) == 0
        and _is_eval_success(cfg, eval_json)
    )

    result = {
        "success": success,
        "agent_returncode": agent_rc,
        "elapsed_sec": elapsed,
        "agent_stdout": agent_stdout,
        "agent_stderr": agent_stderr,
        "thought_trace": thought_trace,
        "test": test_info,
        "eval": eval_json,
        "eval_error": eval_error,
        "runtime_telemetry": telemetry,
    }

    _print_summary(result, verbose=args.verbose)
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
