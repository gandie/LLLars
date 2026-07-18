from __future__ import annotations

import time
from collections.abc import Callable

from lllars_core.config import HarnessConfig, load_config
from lllars_core.runner import run_agent_with_timeout
from lllars_core.runtime import execution, settings
from lllars_core.runtime import results as runtime_results
from lllars_core.runtime.job_runner_flow import canceled_result_or_none
from lllars_core.runtime.job_runner_flow import finalized_result
from lllars_core.runtime.job_runner_flow import resolve_run_context
from lllars_core.runtime.models import JobSpec, RunResult
from lllars_core.shell import (
    ShellSelection,
    detect_shell,
    is_eval_success,
    run_eval,
    run_shell,
    run_tests,
)


class ShellAdapterUnavailableError(RuntimeError):
    def __init__(
        self,
        *,
        shell_mode: str,
        shell_override: str | None,
    ) -> None:
        self.shell_mode = shell_mode
        self.shell_override = shell_override
        super().__init__(
            "No supported shell executable found for "
            f"shell_mode={shell_mode!r}, "
            f"shell_override={shell_override!r}"
        )


def _resolve_shell_selection(cfg: HarnessConfig) -> ShellSelection:
    shell_mode, shell_override = execution.resolve_shell_policy(cfg)
    selection = execution.resolve_shell_selection(
        cfg,
        detect_shell_fn=detect_shell,
    )
    if selection is not None:
        return selection
    raise ShellAdapterUnavailableError(
        shell_mode=shell_mode,
        shell_override=shell_override,
    )


def _run_post_agent(
    cfg: HarnessConfig,
    selection: ShellSelection,
    emit_status: Callable[[str], None] | None,
) -> tuple[dict[str, object], dict[str, object] | None, str | None]:
    return runtime_results.run_post_agent_steps(
        cfg,
        selection,
        emit_status,
        legacy_path_enabled=False,
        run_tests_fn=run_tests,
        run_eval_fn=run_eval,
        run_tests_with_selection_fn=_run_tests_with_selection,
        run_eval_with_selection_fn=_run_eval_with_selection,
    )


def _run_tests_with_selection(
    cfg: HarnessConfig,
    selection: ShellSelection,
) -> dict[str, object]:
    return execution.run_tests_with_selection(
        cfg,
        selection,
        run_shell_fn=run_shell,
    )


def _run_eval_with_selection(
    cfg: HarnessConfig,
    selection: ShellSelection,
) -> tuple[dict[str, object] | None, str | None]:
    return execution.run_eval_with_selection(
        cfg,
        selection,
        run_shell_fn=run_shell,
    )


def _effective_cfg(
    spec: JobSpec,
    cfg: HarnessConfig | None,
) -> HarnessConfig:
    loaded_cfg = cfg or load_config(settings.resolve_config_path(spec))
    return settings.apply_job_run_settings(loaded_cfg, spec)


def _run_agent(
    cfg: HarnessConfig,
    spec: JobSpec,
    show_progress: bool,
    cancel_requested: Callable[[], bool] | None,
) -> tuple[str, str, int, dict[str, object], list[str]]:
    return run_agent_with_timeout(
        cfg=cfg,
        prompt_text=spec.prompt,
        timeout_sec=spec.timeout_sec,
        show_progress=show_progress,
        cancel_requested=cancel_requested,
    )


def _resolve_canceled(
    *,
    cancel_requested: Callable[[], bool] | None,
    start: float,
    outcome: tuple[str, str, int, dict[str, object], list[str]],
    selection: ShellSelection,
    shell_mode: str,
    shell_override: str | None,
) -> RunResult | None:
    return canceled_result_or_none(
        cancel_requested=cancel_requested,
        start=start,
        outcome=outcome,
        selection=selection,
        shell_mode=shell_mode,
        shell_override=shell_override,
    )


def _resolve_context(
    spec: JobSpec,
    cfg: HarnessConfig | None,
) -> tuple[HarnessConfig, str, str | None, ShellSelection]:
    return resolve_run_context(
        spec,
        cfg,
        effective_cfg_fn=_effective_cfg,
        resolve_shell_policy_fn=execution.resolve_shell_policy,
        resolve_shell_selection_fn=_resolve_shell_selection,
    )


def run_job(
    spec: JobSpec,
    *,
    cfg: HarnessConfig | None = None,
    show_progress: bool = False,
    emit_status: Callable[[str], None] | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> RunResult:
    effective_cfg, shell_mode, shell_override, selection = _resolve_context(
        spec,
        cfg,
    )
    start = time.time()
    outcome = _run_agent(effective_cfg, spec, show_progress, cancel_requested)
    canceled = _resolve_canceled(
        cancel_requested=cancel_requested,
        start=start,
        outcome=outcome,
        selection=selection,
        shell_mode=shell_mode,
        shell_override=shell_override,
    )
    if canceled is not None:
        return canceled
    return finalized_result(
        start=start,
        effective_cfg=effective_cfg,
        emit_status=emit_status,
        selection=selection,
        shell_mode=shell_mode,
        shell_override=shell_override,
        outcome=outcome,
        run_post_agent_fn=_run_post_agent,
        is_eval_success_fn=is_eval_success,
    )


__all__ = ["ShellAdapterUnavailableError", "run_job"]
