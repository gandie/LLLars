from __future__ import annotations

import time
from collections.abc import Callable

from lllars_core.runtime.execution import build_runtime_telemetry
from lllars_core.runtime.models import RunResult
from lllars_core.shell import ShellSelection


def run_post_agent_steps(
    cfg: object,
    selection: ShellSelection,
    emit_status: Callable[[str], None] | None,
    *,
    legacy_path_enabled: bool,
    run_tests_fn,
    run_eval_fn,
    run_tests_with_selection_fn,
    run_eval_with_selection_fn,
) -> tuple[dict[str, object], dict[str, object] | None, str | None]:
    _emit_post_agent_status(cfg, emit_status)
    if legacy_path_enabled:
        return run_tests_fn(cfg), *run_eval_fn(cfg)

    test_info = run_tests_with_selection_fn(cfg, selection)
    eval_json, eval_error = run_eval_with_selection_fn(cfg, selection)
    return test_info, eval_json, eval_error


def canceled_result(
    *,
    start: float,
    agent_stdout: str,
    agent_stderr: str,
    agent_rc: int,
    thought_trace: list[str],
    telemetry: dict[str, object],
    selection: ShellSelection,
    shell_mode: str,
    shell_override: str | None,
) -> RunResult:
    return RunResult(
        success=False,
        agent_returncode=agent_rc,
        elapsed_sec=round(time.time() - start, 2),
        agent_stdout=agent_stdout,
        agent_stderr=agent_stderr,
        thought_trace=thought_trace,
        test={},
        eval=None,
        eval_error="canceled",
        runtime_telemetry=_runtime_telemetry(
            telemetry,
            selection,
            shell_mode,
            shell_override,
        ),
    )


def timeout_result(
    *,
    start: float,
    agent_stdout: str,
    agent_stderr: str,
    agent_rc: int,
    thought_trace: list[str],
    telemetry: dict[str, object],
    selection: ShellSelection,
    shell_mode: str,
    shell_override: str | None,
) -> RunResult:
    return RunResult(
        success=False,
        agent_returncode=agent_rc,
        elapsed_sec=round(time.time() - start, 2),
        agent_stdout=agent_stdout,
        agent_stderr=agent_stderr,
        thought_trace=thought_trace,
        test={},
        eval=None,
        eval_error="timeout",
        runtime_telemetry=_runtime_telemetry(
            telemetry,
            selection,
            shell_mode,
            shell_override,
        ),
    )


def _emit_post_agent_status(
    cfg: object,
    emit_status: Callable[[str], None] | None,
) -> None:
    if emit_status is None:
        return
    emit_status(
        "running tests"
        if getattr(cfg, "test_command", None)
        else "tests not configured (skipped)"
    )
    emit_status(
        "running eval"
        if getattr(cfg, "eval_command", None)
        else "eval not configured (skipped)"
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


__all__ = [
    "canceled_result",
    "run_post_agent_steps",
    "timeout_result",
]
