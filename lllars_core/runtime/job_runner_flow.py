from __future__ import annotations

from collections.abc import Callable

from lllars_core.config import HarnessConfig
from lllars_core.runtime import results as runtime_results
from lllars_core.runtime.models import JobSpec, RunResult
from lllars_core.shell import ShellSelection


def resolve_run_context(
    spec: JobSpec,
    cfg: HarnessConfig | None,
    *,
    effective_cfg_fn,
    resolve_shell_policy_fn,
    resolve_shell_selection_fn,
) -> tuple[HarnessConfig, str, str | None, ShellSelection]:
    effective_cfg = effective_cfg_fn(spec, cfg)
    shell_mode, shell_override = resolve_shell_policy_fn(effective_cfg)
    selection = resolve_shell_selection_fn(effective_cfg)
    return effective_cfg, shell_mode, shell_override, selection


def canceled_result_or_none(
    *,
    cancel_requested: Callable[[], bool] | None,
    start: float,
    outcome: tuple[str, str, int, dict[str, object], list[str]],
    selection: ShellSelection,
    shell_mode: str,
    shell_override: str | None,
) -> RunResult | None:
    if cancel_requested is None or not cancel_requested():
        return None
    stdout, stderr, returncode, telemetry, thought_trace = outcome
    return runtime_results.canceled_result(
        start=start,
        agent_stdout=stdout,
        agent_stderr=stderr,
        agent_rc=returncode,
        thought_trace=thought_trace,
        telemetry=telemetry,
        selection=selection,
        shell_mode=shell_mode,
        shell_override=shell_override,
    )


def finalized_result(
    *,
    start: float,
    effective_cfg: HarnessConfig,
    emit_status: Callable[[str], None] | None,
    selection: ShellSelection,
    shell_mode: str,
    shell_override: str | None,
    outcome: tuple[str, str, int, dict[str, object], list[str]],
    run_post_agent_fn,
    is_eval_success_fn,
) -> RunResult:
    stdout, stderr, returncode, telemetry, thought_trace = outcome
    test_info, eval_json, eval_error = run_post_agent_fn(
        effective_cfg,
        selection,
        emit_status,
    )
    return runtime_results.finalized_result(
        start=start,
        agent_stdout=stdout,
        agent_stderr=stderr,
        agent_rc=returncode,
        thought_trace=thought_trace,
        test_info=test_info,
        eval_json=eval_json,
        eval_error=eval_error,
        telemetry=telemetry,
        selection=selection,
        shell_mode=shell_mode,
        shell_override=shell_override,
        cfg=effective_cfg,
        is_eval_success_fn=is_eval_success_fn,
    )


__all__ = [
    "canceled_result_or_none",
    "finalized_result",
    "resolve_run_context",
]
