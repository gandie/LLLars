from __future__ import annotations

from lllars_core.config.models import HarnessConfig, RunConfig, ServiceConfig


def _harness_core_kwargs(
    run_cfg: RunConfig,
    allowed_shell_commands: tuple[str, ...],
    system_prompt: str,
    tool_policy: str,
) -> dict[str, object]:
    return {
        "model": run_cfg.model,
        "provider_url": run_cfg.provider_url,
        "project_root": run_cfg.project_root,
        "test_command": run_cfg.test_command,
        "eval_command": run_cfg.eval_command,
        "eval_expect_json": bool(run_cfg.eval_expect_json),
        "eval_success_pass_rate": float(run_cfg.eval_success_pass_rate),
        "allowed_shell_commands": allowed_shell_commands,
        "system_prompt": system_prompt,
        "tool_policy": tool_policy,
    }


def _harness_usage_kwargs(run_cfg: RunConfig) -> dict[str, object]:
    return {
        "usage_request_limit": run_cfg.usage_request_limit,
        "usage_tool_calls_limit": run_cfg.usage_tool_calls_limit,
        "usage_input_tokens_limit": run_cfg.usage_input_tokens_limit,
        "usage_output_tokens_limit": run_cfg.usage_output_tokens_limit,
        "usage_total_tokens_limit": run_cfg.usage_total_tokens_limit,
        "usage_count_tokens_before_request": bool(
            run_cfg.usage_count_tokens_before_request
        ),
        "agent_retries_tools": int(run_cfg.agent_retries_tools),
        "agent_retries_output": int(run_cfg.agent_retries_output),
        "tool_timeout_sec": run_cfg.tool_timeout_sec,
        "max_concurrency": run_cfg.max_concurrency,
        "instrumentation_enabled": bool(run_cfg.instrumentation_enabled),
        "instrumentation_include_content": bool(
            run_cfg.instrumentation_include_content
        ),
        "skills_enabled": bool(run_cfg.skills_enabled),
        "skills_glob": run_cfg.skills_glob or "",
        "skills_defer_loading": bool(run_cfg.skills_defer_loading),
        "skills_require_description": bool(run_cfg.skills_require_description),
        "mcp_enabled": bool(run_cfg.mcp_enabled),
        "mcp_config_path": run_cfg.mcp_config_path,
        "mcp_init_timeout_sec": float(run_cfg.mcp_init_timeout_sec),
        "shell_mode": run_cfg.shell_mode,
        "shell_override": run_cfg.shell_override,
    }


def _harness_service_kwargs(
    service_cfg: ServiceConfig,
    command_profile: str,
) -> dict[str, object]:
    return {
        "service_mode": service_cfg.mode,
        "service_host": service_cfg.host,
        "service_port": service_cfg.port,
        "service_workers": service_cfg.workers,
        "mount_work_root": service_cfg.mount_work_root,
        "mount_config_root": service_cfg.mount_config_root,
        "mount_artifacts_root": service_cfg.mount_artifacts_root,
        "queue_backend": service_cfg.queue_backend,
        "network_policy": service_cfg.network_policy,
        "command_profile": command_profile,
    }


def _harness_kwargs(
    run_cfg: RunConfig,
    service_cfg: ServiceConfig,
    allowed_shell_commands: tuple[str, ...],
    system_prompt: str,
    tool_policy: str,
    command_profile: str,
) -> dict[str, object]:
    kwargs = _harness_core_kwargs(
        run_cfg,
        allowed_shell_commands,
        system_prompt,
        tool_policy,
    )
    kwargs.update(_harness_usage_kwargs(run_cfg))
    kwargs.update(_harness_service_kwargs(service_cfg, command_profile))
    kwargs["run"] = run_cfg
    kwargs["service"] = service_cfg
    return kwargs


def build_harness_config(
    run_cfg: RunConfig,
    service_cfg: ServiceConfig,
    *,
    allowed_shell_commands: tuple[str, ...],
    system_prompt: str,
    tool_policy: str,
    command_profile: str,
) -> HarnessConfig:
    return HarnessConfig(
        **_harness_kwargs(
            run_cfg,
            service_cfg,
            allowed_shell_commands,
            system_prompt,
            tool_policy,
            command_profile,
        )
    )
