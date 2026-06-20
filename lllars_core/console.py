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


def print_summary(result: dict[str, Any], verbose: bool) -> None:
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
        if isinstance(summary, dict) and isinstance(
            summary.get("pass_rate"), (int, float)
        ):
            eval_text = f"pass_rate={float(summary['pass_rate']):.1f}%"
        else:
            eval_text = "ok"
    elif isinstance(eval_error, str) and eval_error.strip():
        eval_text = f"error: {truncate(eval_error, 90)}"

    print(f"{status_color}{Color.BOLD}{status_text}{Color.RESET}")
    print(
        f"time: {elapsed}s | agent_rc: {agent_rc} "
        f"| test_rc: {test_rc} | eval: {eval_text}"
    )

    if not success:
        stderr_preview = truncate(str(result.get("agent_stderr", "")), 180)
        if stderr_preview:
            print(f"agent_error: {stderr_preview}")

    if not verbose:
        return

    print("\n-- verbose --")
    agent_stdout = str(result.get("agent_stdout", "")).strip()
    if agent_stdout:
        print("agent_output:")
        print(truncate(agent_stdout, 1200))

    agent_stderr = str(result.get("agent_stderr", "")).strip()
    if agent_stderr:
        print("agent_stderr:")
        print(truncate(agent_stderr, 1200))

    print("telemetry:")
    print(json.dumps(result.get("runtime_telemetry", {}), indent=2))

    print("raw_result:")
    print(json.dumps(result, indent=2))
