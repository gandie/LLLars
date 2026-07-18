from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunCommandSettings:
    command_profile: str
    test_command: str | None
    eval_command: str | None
    allowed_shell_commands: tuple[str, ...]


@dataclass(frozen=True)
class ShellRuntimeTelemetry:
    selected: str
    shell_mode: str
    shell_override: str | None
    invocation_mode: str


RUN_CFG_OVERRIDE_FIELDS: tuple[str, ...] = (
    "eval_expect_json",
    "eval_success_pass_rate",
    "system_prompt",
    "tool_policy",
    "usage_request_limit",
    "usage_tool_calls_limit",
    "usage_input_tokens_limit",
    "usage_output_tokens_limit",
    "usage_total_tokens_limit",
    "usage_count_tokens_before_request",
    "agent_retries_tools",
    "agent_retries_output",
    "tool_timeout_sec",
    "max_concurrency",
    "instrumentation_enabled",
    "instrumentation_include_content",
    "skills_enabled",
    "skills_glob",
    "skills_defer_loading",
    "skills_require_description",
    "mcp_enabled",
    "mcp_config_path",
    "mcp_init_timeout_sec",
    "shell_mode",
    "shell_override",
)


HARNESS_RUN_SYNC_FIELDS: tuple[str, ...] = (
    "eval_expect_json",
    "eval_success_pass_rate",
    "system_prompt",
    "tool_policy",
    "usage_request_limit",
    "usage_tool_calls_limit",
    "usage_input_tokens_limit",
    "usage_output_tokens_limit",
    "usage_total_tokens_limit",
    "usage_count_tokens_before_request",
    "agent_retries_tools",
    "agent_retries_output",
    "tool_timeout_sec",
    "max_concurrency",
    "instrumentation_enabled",
    "instrumentation_include_content",
    "skills_enabled",
    "skills_glob",
    "skills_defer_loading",
    "skills_require_description",
    "mcp_enabled",
    "mcp_init_timeout_sec",
    "shell_mode",
    "shell_override",
)


__all__ = [
    "HARNESS_RUN_SYNC_FIELDS",
    "RUN_CFG_OVERRIDE_FIELDS",
    "RunCommandSettings",
    "ShellRuntimeTelemetry",
]
