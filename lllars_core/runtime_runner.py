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
from lllars_core.shell import (
    ShellSelection,
    detect_shell,
    is_eval_success,
    run_eval,
    run_shell,
    run_tests,
)


ENABLE_LEGACY_SHELL_EXECUTION_PATH = False


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


def _command_cwd(cfg: HarnessConfig) -> Path:
    project_root = getattr(cfg, "project_root", None)
    if isinstance(project_root, Path):
        return project_root
    return Path.cwd()


def _resolve_shell_policy(cfg: HarnessConfig) -> tuple[str, str | None]:
    shell_mode_raw = getattr(cfg, "shell_mode", "auto")
    shell_mode = str(shell_mode_raw).strip().lower() or "auto"
    shell_override_raw = getattr(cfg, "shell_override", None)
    shell_override = (
        str(shell_override_raw).strip().lower()
        if isinstance(shell_override_raw, str)
        and shell_override_raw.strip()
        else None
    )
    return shell_mode, shell_override


def _resolve_shell_selection(cfg: HarnessConfig) -> ShellSelection:
    shell_mode, shell_override = _resolve_shell_policy(cfg)
    selection = detect_shell(
        shell_mode=shell_mode,
        shell_override=shell_override,
    )
    if selection is None:
        raise ShellAdapterUnavailableError(
            shell_mode=shell_mode,
            shell_override=shell_override,
        )
    return selection


def _shell_invocation_mode(shell_mode: str) -> str:
    return "explicit_override" if shell_mode == "override" else "auto_detect"


def _run_tests_with_selection(
    cfg: HarnessConfig,
    selection: ShellSelection,
) -> dict[str, object]:
    if cfg.test_command is None:
        return {
            "returncode": 0,
            "stdout": "",
            "stderr": "tests not configured",
            "skipped": True,
            "shell": selection.name,
        }
    payload = run_shell(
        command=cfg.test_command,
        cwd=_command_cwd(cfg),
        timeout_sec=120,
        shell_mode="override",
        shell_override=selection.name,
    )
    return payload


def _run_eval_with_selection(
    cfg: HarnessConfig,
    selection: ShellSelection,
) -> tuple[dict[str, object] | None, str | None]:
    if cfg.eval_command is None:
        return None, None

    payload = run_shell(
        command=cfg.eval_command,
        cwd=_command_cwd(cfg),
        timeout_sec=120,
        shell_mode="override",
        shell_override=selection.name,
    )
    if int(payload.get("returncode", 1)) != 0:
        return None, str(payload.get("stderr", ""))

    if not bool(getattr(cfg, "eval_expect_json", True)):
        return {
            "raw_stdout": str(payload.get("stdout", "")),
            "raw_stderr": str(payload.get("stderr", "")),
            "returncode": int(payload.get("returncode", 0)),
            "shell": selection.name,
        }, None

    import json

    try:
        parsed = json.loads(str(payload.get("stdout", "")))
    except Exception as exc:
        return None, str(exc)

    if not isinstance(parsed, dict):
        return None, None
    parsed.setdefault("shell", selection.name)
    return parsed, None


def _resolve_config_path(spec: JobSpec) -> Path:
    if spec.config_path is None:
        return DEFAULT_CONFIG_PATH.resolve()
    return Path(spec.config_path).resolve()


def _apply_job_run_settings(
    cfg: HarnessConfig,
    spec: JobSpec,
) -> HarnessConfig:
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
                "Invalid project_root: "
                f"{resolved_project_root} escapes mount_work_root"
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

    run_commands = spec.run.commands or {}
    test_raw = spec.run.test_command
    if test_raw is None and isinstance(run_commands, dict):
        test_raw = run_commands.get("test")
    eval_raw = spec.run.eval_command
    if eval_raw is None and isinstance(run_commands, dict):
        eval_raw = run_commands.get("eval")

    test_command = (
        test_raw.strip()
        if isinstance(test_raw, str) and test_raw.strip()
        else None
    )
    eval_command = (
        eval_raw.strip()
        if isinstance(eval_raw, str) and eval_raw.strip()
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
        commands={
            key: value
            for key, value in {
                "test": test_command,
                "eval": eval_command,
            }.items()
            if value is not None
        },
        test_command=test_command,
        eval_command=eval_command,
        command_profile=command_profile,
        eval_expect_json=(
            cfg.eval_expect_json
            if spec.run.eval_expect_json is None
            else spec.run.eval_expect_json
        ),
        eval_success_pass_rate=(
            cfg.eval_success_pass_rate
            if spec.run.eval_success_pass_rate is None
            else spec.run.eval_success_pass_rate
        ),
        system_prompt=(
            cfg.system_prompt
            if spec.run.system_prompt is None
            else spec.run.system_prompt
        ),
        tool_policy=(
            cfg.tool_policy
            if spec.run.tool_policy is None
            else spec.run.tool_policy
        ),
        usage_request_limit=(
            cfg.usage_request_limit
            if spec.run.usage_request_limit is None
            else spec.run.usage_request_limit
        ),
        usage_tool_calls_limit=(
            cfg.usage_tool_calls_limit
            if spec.run.usage_tool_calls_limit is None
            else spec.run.usage_tool_calls_limit
        ),
        usage_input_tokens_limit=(
            cfg.usage_input_tokens_limit
            if spec.run.usage_input_tokens_limit is None
            else spec.run.usage_input_tokens_limit
        ),
        usage_output_tokens_limit=(
            cfg.usage_output_tokens_limit
            if spec.run.usage_output_tokens_limit is None
            else spec.run.usage_output_tokens_limit
        ),
        usage_total_tokens_limit=(
            cfg.usage_total_tokens_limit
            if spec.run.usage_total_tokens_limit is None
            else spec.run.usage_total_tokens_limit
        ),
        usage_count_tokens_before_request=(
            cfg.usage_count_tokens_before_request
            if spec.run.usage_count_tokens_before_request is None
            else spec.run.usage_count_tokens_before_request
        ),
        agent_retries_tools=(
            cfg.agent_retries_tools
            if spec.run.agent_retries_tools is None
            else spec.run.agent_retries_tools
        ),
        agent_retries_output=(
            cfg.agent_retries_output
            if spec.run.agent_retries_output is None
            else spec.run.agent_retries_output
        ),
        tool_timeout_sec=(
            cfg.tool_timeout_sec
            if spec.run.tool_timeout_sec is None
            else spec.run.tool_timeout_sec
        ),
        max_concurrency=(
            cfg.max_concurrency
            if spec.run.max_concurrency is None
            else spec.run.max_concurrency
        ),
        instrumentation_enabled=(
            cfg.instrumentation_enabled
            if spec.run.instrumentation_enabled is None
            else spec.run.instrumentation_enabled
        ),
        instrumentation_include_content=(
            cfg.instrumentation_include_content
            if spec.run.instrumentation_include_content is None
            else spec.run.instrumentation_include_content
        ),
        skills_enabled=(
            cfg.skills_enabled
            if spec.run.skills_enabled is None
            else spec.run.skills_enabled
        ),
        skills_glob=(
            cfg.skills_glob
            if spec.run.skills_glob is None
            else spec.run.skills_glob
        ),
        skills_defer_loading=(
            cfg.skills_defer_loading
            if spec.run.skills_defer_loading is None
            else spec.run.skills_defer_loading
        ),
        skills_require_description=(
            cfg.skills_require_description
            if spec.run.skills_require_description is None
            else spec.run.skills_require_description
        ),
        mcp_enabled=(
            cfg.mcp_enabled
            if spec.run.mcp_enabled is None
            else spec.run.mcp_enabled
        ),
        mcp_config_path=(
            cfg.mcp_config_path
            if spec.run.mcp_config_path is None
            else spec.run.mcp_config_path
        ),
        mcp_init_timeout_sec=(
            cfg.mcp_init_timeout_sec
            if spec.run.mcp_init_timeout_sec is None
            else spec.run.mcp_init_timeout_sec
        ),
        shell_mode=(
            cfg.shell_mode
            if spec.run.shell_mode is None
            else spec.run.shell_mode
        ),
        shell_override=(
            cfg.shell_override
            if spec.run.shell_override is None
            else spec.run.shell_override
        ),
    )

    run_mcp_config_path = run_cfg.mcp_config_path
    if (
        run_mcp_config_path is not None
        and not run_mcp_config_path.is_absolute()
    ):
        run_mcp_config_path = (
            cfg.mount_config_root / run_mcp_config_path
        ).resolve()
    if run_cfg.mcp_enabled and run_mcp_config_path is None:
        raise ValueError(
            "mcp_enabled is true but mcp_config_path is empty"
        )
    if run_cfg.mcp_enabled and run_mcp_config_path is not None:
        if (
            not run_mcp_config_path.exists()
            or not run_mcp_config_path.is_file()
        ):
            raise ValueError(
                f"Invalid mcp_config_path: {run_mcp_config_path}"
            )
    if run_cfg.skills_enabled and not (run_cfg.skills_glob or "").strip():
        raise ValueError("skills_enabled is true but skills_glob is empty")

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
            eval_expect_json=run_cfg.eval_expect_json,
            eval_success_pass_rate=run_cfg.eval_success_pass_rate,
            system_prompt=run_cfg.system_prompt,
            tool_policy=run_cfg.tool_policy,
            usage_request_limit=run_cfg.usage_request_limit,
            usage_tool_calls_limit=run_cfg.usage_tool_calls_limit,
            usage_input_tokens_limit=run_cfg.usage_input_tokens_limit,
            usage_output_tokens_limit=run_cfg.usage_output_tokens_limit,
            usage_total_tokens_limit=run_cfg.usage_total_tokens_limit,
            usage_count_tokens_before_request=(
                run_cfg.usage_count_tokens_before_request
            ),
            agent_retries_tools=run_cfg.agent_retries_tools,
            agent_retries_output=run_cfg.agent_retries_output,
            tool_timeout_sec=run_cfg.tool_timeout_sec,
            max_concurrency=run_cfg.max_concurrency,
            instrumentation_enabled=run_cfg.instrumentation_enabled,
            instrumentation_include_content=(
                run_cfg.instrumentation_include_content
            ),
            skills_enabled=run_cfg.skills_enabled,
            skills_glob=(run_cfg.skills_glob or ""),
            skills_defer_loading=run_cfg.skills_defer_loading,
            skills_require_description=run_cfg.skills_require_description,
            mcp_enabled=run_cfg.mcp_enabled,
            mcp_config_path=run_mcp_config_path,
            mcp_init_timeout_sec=run_cfg.mcp_init_timeout_sec,
            shell_mode=run_cfg.shell_mode,
            shell_override=run_cfg.shell_override,
            run=run_cfg,
        )
    return cfg


def run_job(
    spec: JobSpec,
    *,
    cfg: HarnessConfig | None = None,
    show_progress: bool = False,
    emit_status: Callable[[str], None] | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> RunResult:
    effective_cfg = cfg
    if effective_cfg is None:
        effective_cfg = load_config(_resolve_config_path(spec))
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
        runtime_telemetry = dict(telemetry)
        runtime_telemetry["shell"] = {
            "selected": selection.name,
            "shell_mode": shell_mode,
            "shell_override": shell_override,
            "invocation_mode": _shell_invocation_mode(shell_mode),
        }
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
            runtime_telemetry=runtime_telemetry,
        )

    if ENABLE_LEGACY_SHELL_EXECUTION_PATH:
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
    else:
        if emit_status is not None:
            if effective_cfg.test_command:
                emit_status("running tests")
            else:
                emit_status("tests not configured (skipped)")
        test_info = _run_tests_with_selection(effective_cfg, selection)

        if emit_status is not None:
            if effective_cfg.eval_command:
                emit_status("running eval")
            else:
                emit_status("eval not configured (skipped)")
        eval_json, eval_error = _run_eval_with_selection(
            effective_cfg,
            selection,
        )

    runtime_telemetry = dict(telemetry)
    runtime_telemetry["shell"] = {
        "selected": selection.name,
        "shell_mode": shell_mode,
        "shell_override": shell_override,
        "invocation_mode": _shell_invocation_mode(shell_mode),
    }

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
        runtime_telemetry=runtime_telemetry,
    )
