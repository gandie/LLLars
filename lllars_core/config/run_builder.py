from __future__ import annotations

from pathlib import Path

from lllars_core.config.models import (
    DEFAULT_AGENT_RETRIES_OUTPUT,
    DEFAULT_AGENT_RETRIES_TOOLS,
    DEFAULT_TOOL_TIMEOUT_SEC,
    DEFAULT_USAGE_TOOL_CALLS_LIMIT,
    RunConfig,
)
from lllars_core.config.runtime_section import (
    as_bool,
    non_negative_int,
    optional_float,
    optional_int,
)


def _run_usage_kwargs(cfg: dict) -> dict[str, object]:
    return {
        "usage_request_limit": optional_int(cfg, "usage_request_limit", None),
        "usage_tool_calls_limit": optional_int(
            cfg,
            "usage_tool_calls_limit",
            DEFAULT_USAGE_TOOL_CALLS_LIMIT,
        ),
        "usage_input_tokens_limit": optional_int(
            cfg,
            "usage_input_tokens_limit",
            None,
        ),
        "usage_output_tokens_limit": optional_int(
            cfg,
            "usage_output_tokens_limit",
            None,
        ),
        "usage_total_tokens_limit": optional_int(
            cfg,
            "usage_total_tokens_limit",
            None,
        ),
        "usage_count_tokens_before_request": as_bool(
            cfg.get("usage_count_tokens_before_request", False),
            False,
        ),
    }


def _run_retry_and_runtime_kwargs(cfg: dict) -> dict[str, object]:
    return {
        "agent_retries_tools": non_negative_int(
            cfg,
            "agent_retries_tools",
            DEFAULT_AGENT_RETRIES_TOOLS,
        ),
        "agent_retries_output": non_negative_int(
            cfg,
            "agent_retries_output",
            DEFAULT_AGENT_RETRIES_OUTPUT,
        ),
        "tool_timeout_sec": optional_float(
            cfg,
            "tool_timeout_sec",
            DEFAULT_TOOL_TIMEOUT_SEC,
        ),
        "max_concurrency": optional_int(cfg, "max_concurrency", None),
        "instrumentation_enabled": as_bool(
            cfg.get("instrumentation_enabled", False),
            False,
        ),
        "instrumentation_include_content": as_bool(
            cfg.get("instrumentation_include_content", False),
            False,
        ),
    }


def _command_map(
    test_command: str | None,
    eval_command: str | None,
) -> dict[str, str]:
    commands: dict[str, str] = {}
    if test_command is not None:
        commands["test"] = test_command
    if eval_command is not None:
        commands["eval"] = eval_command
    return commands


def _skills_kwargs(
    settings: tuple[bool, str, bool, bool],
) -> dict[str, object]:
    enabled, glob, defer_loading, require_description = settings
    return {
        "skills_enabled": enabled,
        "skills_glob": glob,
        "skills_defer_loading": defer_loading,
        "skills_require_description": require_description,
    }


def _mcp_kwargs(
    settings: tuple[bool, Path | None, float],
) -> dict[str, object]:
    enabled, path, timeout = settings
    return {
        "mcp_enabled": enabled,
        "mcp_config_path": path,
        "mcp_init_timeout_sec": timeout,
    }


def _shell_kwargs(settings: tuple[str, str | None]) -> dict[str, object]:
    shell_mode, shell_override = settings
    return {
        "shell_mode": shell_mode,
        "shell_override": shell_override,
    }


def build_run_config(
    cfg: dict,
    *,
    model: str,
    provider_url: str,
    project_root: Path,
    test_command: str | None,
    eval_command: str | None,
    command_profile: str,
    system_prompt: str,
    tool_policy: str,
    eval_expect_json: bool,
    eval_success_pass_rate: float,
    skills_settings: tuple[bool, str, bool, bool],
    mcp_settings: tuple[bool, Path | None, float],
    shell_settings: tuple[str, str | None],
) -> RunConfig:
    return RunConfig(
        model=model,
        provider_url=provider_url,
        project_root=project_root,
        commands=_command_map(test_command, eval_command),
        test_command=test_command,
        eval_command=eval_command,
        command_profile=command_profile,
        eval_expect_json=eval_expect_json,
        eval_success_pass_rate=eval_success_pass_rate,
        system_prompt=system_prompt,
        tool_policy=tool_policy,
        **_skills_kwargs(skills_settings),
        **_mcp_kwargs(mcp_settings),
        **_shell_kwargs(shell_settings),
        **_run_usage_kwargs(cfg),
        **_run_retry_and_runtime_kwargs(cfg),
    )
