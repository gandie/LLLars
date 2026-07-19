from __future__ import annotations

import time

from lllars_core.runtime.execution import build_runtime_telemetry
from lllars_core.runtime.models import RunResult
from lllars_core.shell import ShellSelection


def finalized_result(
    *,
    start: float,
    agent_stdout: str,
    agent_stderr: str,
    agent_rc: int,
    thought_trace: list[str],
    test_info: dict[str, object],
    eval_json: dict[str, object] | None,
    eval_error: str | None,
    telemetry: dict[str, object],
    selection: ShellSelection,
    shell_mode: str,
    shell_override: str | None,
    cfg: object,
    is_eval_success_fn,
) -> RunResult:
    return RunResult(**_finalized_payload(locals()))


def _finalized_payload(data: dict[str, object]) -> dict[str, object]:
    agent_rc = int(data["agent_rc"])
    test_info = data["test_info"]
    eval_json = data["eval_json"]
    return {
        "success": _is_success(
            agent_rc,
            test_info,
            data["cfg"],
            eval_json,
            data["is_eval_success_fn"],
        ),
        "agent_returncode": agent_rc,
        "elapsed_sec": round(time.time() - float(data["start"]), 2),
        "agent_stdout": data["agent_stdout"],
        "agent_stderr": data["agent_stderr"],
        "thought_trace": data["thought_trace"],
        "test": test_info,
        "eval": eval_json,
        "eval_error": data["eval_error"],
        "runtime_telemetry": _runtime_telemetry(
            data["telemetry"],
            data["selection"],
            str(data["shell_mode"]),
            data["shell_override"],
        ),
    }


def _is_success(
    agent_rc: int,
    test_info: dict[str, object],
    cfg: object,
    eval_json: dict[str, object] | None,
    is_eval_success_fn,
) -> bool:
    return (
        agent_rc == 0
        and int(test_info.get("returncode", 1)) == 0
        and is_eval_success_fn(cfg, eval_json)
    )


def _runtime_telemetry(
    telemetry: dict[str, object],
    selection: ShellSelection,
    shell_mode: str,
    shell_override: str | None,
) -> dict[str, object]:
    runtime_telemetry = dict(telemetry)
    runtime_telemetry["shell"] = build_runtime_telemetry(
        selection,
        shell_mode,
        shell_override,
    )
    return runtime_telemetry


__all__ = ["finalized_result"]
