from __future__ import annotations

from dataclasses import is_dataclass, replace
import time
from collections.abc import Callable
from pathlib import Path

from lllars_core.config import (
    COMMAND_PROFILE_REGISTRY,
    DEFAULT_CONFIG_PATH,
    HarnessConfig,
    RunConfig,
    canonicalize_shell_command,
    load_config,
)
from lllars_core.runtime_guard import resolve_project_root
from lllars_core.runner import run_agent_with_timeout
from lllars_core.runtime_models import JobSpec, RunResult
from lllars_core.shell import is_eval_success, run_eval, run_tests


def _resolve_config_path(spec: JobSpec) -> Path:
    if spec.config_path is None:
        return DEFAULT_CONFIG_PATH.resolve()
    return Path(spec.config_path).resolve()


def _apply_job_run_settings(cfg: HarnessConfig, spec: JobSpec) -> HarnessConfig:
    if not hasattr(cfg, "mount_work_root"):
        return cfg

    mount_root = cfg.mount_work_root.resolve()
    run_project_root = spec.run.project_root
    if run_project_root.is_absolute():
        resolved_project_root = run_project_root.resolve()
        try:
            resolved_project_root.relative_to(mount_root)
        except ValueError as exc:
            raise ValueError(
                f"Invalid project_root: {resolved_project_root} escapes mount_work_root"
            ) from exc
    else:
        resolved_project_root = resolve_project_root(
            str(run_project_root),
            config_root=mount_root,
            mount_work_root=mount_root,
        )

    command_profile = (
        (spec.run.command_profile or "").strip().lower()
        or cfg.command_profile
    )
    if command_profile not in COMMAND_PROFILE_REGISTRY:
        available = ", ".join(sorted(COMMAND_PROFILE_REGISTRY))
        raise ValueError(
            "Unknown command_profile "
            f"{command_profile!r}. Available profiles: {available}"
        )

    test_command = (
        spec.run.test_command.strip()
        if isinstance(spec.run.test_command, str)
        and spec.run.test_command.strip()
        else None
    )
    eval_command = (
        spec.run.eval_command.strip()
        if isinstance(spec.run.eval_command, str)
        and spec.run.eval_command.strip()
        else None
    )

    seen: set[str] = set()
    allowed: list[str] = []

    def _add_allowed(raw_command: str | None) -> None:
        if raw_command is None:
            return
        canonical = canonicalize_shell_command(raw_command)
        if canonical and canonical not in seen:
            seen.add(canonical)
            allowed.append(canonical)

    _add_allowed(test_command)
    _add_allowed(eval_command)
    for profile_command in COMMAND_PROFILE_REGISTRY[command_profile]:
        _add_allowed(profile_command)

    run_cfg = RunConfig(
        model=spec.run.model,
        provider_url=spec.run.provider_url,
        project_root=resolved_project_root,
        test_command=test_command,
        eval_command=eval_command,
        command_profile=command_profile,
    )

    if is_dataclass(cfg):
        return replace(
            cfg,
            model=spec.run.model,
            provider_url=spec.run.provider_url,
            project_root=resolved_project_root,
            test_command=test_command,
            eval_command=eval_command,
            command_profile=command_profile,
            allowed_shell_commands=tuple(allowed),
            run=run_cfg,
        )
    return cfg


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
    effective_cfg = _apply_job_run_settings(effective_cfg, spec)

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
