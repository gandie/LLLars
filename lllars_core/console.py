from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def truncate(value: str, max_len: int = 220) -> str:
    text = value.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def append_trace(trace: list[str], message: str, limit: int = 24) -> None:
    clean = truncate(message, 180)
    if not clean:
        return
    if trace and trace[-1] == clean:
        return
    trace.append(clean)
    if len(trace) > limit:
        del trace[:-limit]


def _read_tool_name(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _format_part_start_event(event: Any) -> str:
    part = getattr(event, "part", None)
    part_kind = part.__class__.__name__.replace("Part", "")
    tool_name = _read_tool_name(getattr(part, "tool_name", None))
    if tool_name:
        return f"model: started tool call part ({tool_name})"
    return f"model: started {part_kind.lower()} part"


def _format_function_tool_call(event: Any) -> str:
    part = getattr(event, "part", None)
    tool_name = _read_tool_name(getattr(part, "tool_name", None))
    args = getattr(part, "args", None)
    args_preview = truncate(
        json.dumps(args) if isinstance(args, dict) else str(args),
        120,
    )
    if tool_name:
        return f"tool: call {tool_name} args={args_preview}"
    return "tool: call"


def _format_tool_result(event: Any) -> str:
    part = getattr(event, "part", None)
    tool_name = _read_tool_name(getattr(part, "tool_name", None))
    if tool_name:
        return f"tool: result {tool_name}"
    return "tool: result"


def _format_builtin_tool_call(event: Any) -> str:
    part = getattr(event, "part", None)
    tool_name = _read_tool_name(getattr(part, "tool_name", None))
    if tool_name:
        return f"native-tool: call {tool_name}"
    return "native-tool: call"


def _format_builtin_tool_result(event: Any) -> str:
    result = getattr(event, "result", None)
    tool_name = _read_tool_name(getattr(result, "tool_name", None))
    if tool_name:
        return f"native-tool: result {tool_name}"
    return "native-tool: result"


def summarize_agent_stream_event(event: Any) -> str | None:
    kind = event.__class__.__name__
    handlers = {
        "PartStartEvent": _format_part_start_event,
        "FunctionToolCallEvent": _format_function_tool_call,
        "FunctionToolResultEvent": _format_tool_result,
        "BuiltinToolCallEvent": _format_builtin_tool_call,
        "BuiltinToolResultEvent": _format_builtin_tool_result,
    }
    if kind == "FinalResultEvent":
        return "model: final result started"
    handler = handlers.get(kind)
    return handler(event) if handler else None


def emit_live_thought(message: str, thought_log_path: Path | None) -> None:
    if thought_log_path is None:
        return
    try:
        with thought_log_path.open("a", encoding="utf-8") as handle:
            handle.write(truncate(message, 180) + "\n")
    except Exception:
        return


def extract_thought_trace(result: Any) -> list[str]:
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
                    trace.append(truncate(text, 180))
                tool_name = getattr(part, "tool_name", None)
                if isinstance(tool_name, str) and tool_name:
                    trace.append(f"tool-call: {tool_name}")
            if len(trace) >= 12:
                break
    except Exception:
        return []
    return trace[:12]


def _eval_text(result: dict[str, Any]) -> str:
    eval_json = result.get("eval")
    eval_error = result.get("eval_error")
    if isinstance(eval_json, dict):
        summary = eval_json.get("summary")
        if isinstance(summary, dict) and isinstance(
            summary.get("pass_rate"), (int, float)
        ):
            return f"pass_rate={float(summary['pass_rate']):.1f}%"
        return "ok"
    if isinstance(eval_error, str) and eval_error.strip():
        return f"error: {truncate(eval_error, 90)}"
    return "skipped"


def _skill_telemetry(runtime_telemetry: Any) -> tuple[int, str, int, str]:
    if not isinstance(runtime_telemetry, dict):
        return 0, "none", 0, "none"
    loaded_ids = runtime_telemetry.get("skills_loaded_ids", [])
    used_ids = runtime_telemetry.get("skills_used_ids", [])
    loaded_count = int(runtime_telemetry.get("skills_loaded_count", 0))
    used_count = int(runtime_telemetry.get("skills_used_count", 0))
    loaded_text = ", ".join(str(item) for item in loaded_ids) or "none"
    used_text = ", ".join(str(item) for item in used_ids) or "none"
    return loaded_count, loaded_text, used_count, used_text


def _print_verbose(result: dict[str, Any], runtime_telemetry: Any) -> None:
    print("\n-- verbose --")
    agent_stderr = str(result.get("agent_stderr", "")).strip()
    if agent_stderr:
        print("agent_stderr:")
        print(truncate(agent_stderr, 1200))
    print("telemetry:")
    print(json.dumps(runtime_telemetry, indent=2))
    print("raw_result:")
    print(json.dumps(result, indent=2))


def _print_result_body(result: dict[str, Any], success: bool) -> None:
    if not success:
        stderr_preview = truncate(str(result.get("agent_stderr", "")), 180)
        if stderr_preview:
            print(f"agent_error: {stderr_preview}")
    agent_stdout = str(result.get("agent_stdout", "")).strip()
    if agent_stdout:
        print("agent_output:")
        print(truncate(agent_stdout, 1200))


def print_summary(result: dict[str, Any], verbose: bool) -> None:
    success = bool(result.get("success", False))
    status_text = "SUCCESS" if success else "FAILED"
    status_color = Color.GREEN if success else Color.RED

    elapsed = result.get("elapsed_sec", "?")
    agent_rc = int(result.get("agent_returncode", 125))
    test = result.get("test", {})
    test_rc = int(test.get("returncode", 1)) if isinstance(test, dict) else 1
    eval_text = _eval_text(result)

    runtime_telemetry = result.get("runtime_telemetry", {})
    loaded_count, loaded_text, used_count, used_text = _skill_telemetry(
        runtime_telemetry
    )

    print(f"{status_color}{Color.BOLD}{status_text}{Color.RESET}")
    print(
        f"time: {elapsed}s | agent_rc: {agent_rc} "
        f"| test_rc: {test_rc} | eval: {eval_text}"
    )
    print(
        f"skills_loaded={loaded_count} [{loaded_text}] | "
        f"skills_used={used_count} [{used_text}]"
    )
    _print_result_body(result, success)

    if not verbose:
        return
    _print_verbose(result, runtime_telemetry)
