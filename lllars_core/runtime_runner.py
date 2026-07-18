from __future__ import annotations

import time
from collections.abc import Callable

from lllars_core.config import HarnessConfig, load_config
from lllars_core.runner import run_agent_with_timeout
from lllars_core.runtime import execution, settings
from lllars_core.runtime import results as runtime_results
from lllars_core.runtime_models import JobSpec, RunResult
from lllars_core.shell import (
    ShellSelection,
    detect_shell,
    is_eval_success,
    run_eval,
    run_shell,
    run_tests,
)


ENABLE_LEGACY_SHELL_EXECUTION_PATH = False
IMPORT_MIGRATION_NOTE = (
    "Preferred import path: lllars_core.runtime.run_job and "
    "lllars_core.runtime.ShellAdapterUnavailableError"
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


def _command_cwd(cfg: HarnessConfig):
    return execution.command_cwd(cfg)


def _resolve_shell_policy(cfg: HarnessConfig) -> tuple[str, str | None]:
    return execution.resolve_shell_policy(cfg)


def _resolve_shell_selection(cfg: HarnessConfig) -> ShellSelection:
    shell_mode, shell_override = _resolve_shell_policy(cfg)
    selection = execution.resolve_shell_selection(
        cfg,
        detect_shell_fn=detect_shell,
    )
    if selection is None:
        raise ShellAdapterUnavailableError(
            shell_mode=shell_mode,
            shell_override=shell_override,
        )
    return selection


def _shell_invocation_mode(shell_mode: str) -> str:
    return execution.shell_invocation_mode(shell_mode)


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


def _resolve_config_path(spec: JobSpec):
    return settings.resolve_config_path(spec)


def _apply_job_run_settings(
    cfg: HarnessConfig,
    spec: JobSpec,
) -> HarnessConfig:
    return settings.apply_job_run_settings(cfg, spec)


def run_job(
    spec: JobSpec,
    *,
    cfg: HarnessConfig | None = None,
    show_progress: bool = False,
    emit_status: Callable[[str], None] | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> RunResult:
    effective_cfg = cfg or load_config(_resolve_config_path(spec))
    effective_cfg = _apply_job_run_settings(effective_cfg, spec)

    shell_mode, shell_override = _resolve_shell_policy(effective_cfg)
    selection = _resolve_shell_selection(effective_cfg)

    start = time.time()
    (
        agent_stdout,
        agent_stderr,
        agent_rc,
        telemetry,
        thought_trace,
    ) = run_agent_with_timeout(
        cfg=effective_cfg,
        prompt_text=spec.prompt,
        timeout_sec=spec.timeout_sec,
        show_progress=show_progress,
        cancel_requested=cancel_requested,
    )

    if cancel_requested is not None and cancel_requested():
        return runtime_results.canceled_result(
            start=start,
            agent_stdout=agent_stdout,
            agent_stderr=agent_stderr,
            agent_rc=agent_rc,
            thought_trace=thought_trace,
            telemetry=telemetry,
            selection=selection,
            shell_mode=shell_mode,
            shell_override=shell_override,
        )

    test_info, eval_json, eval_error = runtime_results.run_post_agent_steps(
        effective_cfg,
        selection,
        emit_status,
        legacy_path_enabled=ENABLE_LEGACY_SHELL_EXECUTION_PATH,
        run_tests_fn=run_tests,
        run_eval_fn=run_eval,
        run_tests_with_selection_fn=_run_tests_with_selection,
        run_eval_with_selection_fn=_run_eval_with_selection,
    )
    return runtime_results.finalized_result(
        start=start,
        agent_stdout=agent_stdout,
        agent_stderr=agent_stderr,
        agent_rc=agent_rc,
        thought_trace=thought_trace,
        test_info=test_info,
        eval_json=eval_json,
        eval_error=eval_error,
        telemetry=telemetry,
        selection=selection,
        shell_mode=shell_mode,
        shell_override=shell_override,
        cfg=effective_cfg,
        is_eval_success_fn=is_eval_success,
    )


__all__ = [
    "ENABLE_LEGACY_SHELL_EXECUTION_PATH",
    "IMPORT_MIGRATION_NOTE",
    "ShellAdapterUnavailableError",
    "run_job",
]
