from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from lllars_core.config import DEFAULT_CONFIG_PATH, HarnessConfig, load_config
from lllars_core.runner import run_agent_with_timeout
from lllars_core.runtime_models import JobSpec, RunResult
from lllars_core.shell import is_eval_success, run_eval, run_tests


def _resolve_config_path(spec: JobSpec) -> Path:
    if spec.config_path is None:
        return DEFAULT_CONFIG_PATH.resolve()
    return Path(spec.config_path).resolve()


def run_job(
    spec: JobSpec,
    *,
    cfg: HarnessConfig | None = None,
    show_progress: bool = False,
    emit_status: Callable[[str], None] | None = None,
) -> RunResult:
    effective_cfg = cfg
    if effective_cfg is None:
        effective_cfg = load_config(_resolve_config_path(spec))

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
    )

    if emit_status is not None:
        if effective_cfg.test_command:
            emit_status("running tests")
        else:
            emit_status("tests not configured (skipped)")
    test_info = run_tests(effective_cfg)

    if emit_status is not None:
        if effective_cfg.eval_command:
            emit_status("running eval")
        else:
            emit_status("eval not configured (skipped)")
    eval_json, eval_error = run_eval(effective_cfg)

    success = (
        agent_rc == 0
        and int(test_info.get("returncode", 1)) == 0
        and is_eval_success(effective_cfg, eval_json)
    )

    return RunResult(
        success=success,
        agent_returncode=agent_rc,
        elapsed_sec=round(time.time() - start, 2),
        agent_stdout=agent_stdout,
        agent_stderr=agent_stderr,
        thought_trace=thought_trace,
        test=test_info,
        eval=eval_json,
        eval_error=eval_error,
        runtime_telemetry=telemetry,
    )
