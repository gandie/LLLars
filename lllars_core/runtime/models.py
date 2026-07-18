from __future__ import annotations

from typing import Any, Literal

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from lllars_core.config import RunConfig


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


JobState = Literal[
    "queued",
    "running",
    "succeeded",
    "failed",
    "canceled",
]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JobSpec(_StrictModel):
    prompt: str = Field(min_length=1)
    run: RunConfig
    timeout_sec: int = Field(default=600, gt=0)
    config_path: str | None = None


class RunResult(_StrictModel):
    success: bool
    agent_returncode: int
    elapsed_sec: float = Field(ge=0)
    agent_stdout: str
    agent_stderr: str
    thought_trace: list[str] = Field(default_factory=list)
    test: dict[str, Any] = Field(default_factory=dict)
    eval: dict[str, Any] | None = None
    eval_error: str | None = None
    runtime_telemetry: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(_StrictModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, Any] | None = None


class JobStatus(_StrictModel):
    job_id: str = Field(min_length=1)
    status: JobState
    result: RunResult | None = None
    error: ErrorEnvelope | None = None


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
    "ErrorEnvelope",
    "HARNESS_RUN_SYNC_FIELDS",
    "JobSpec",
    "JobState",
    "JobStatus",
    "RUN_CFG_OVERRIDE_FIELDS",
    "RunCommandSettings",
    "RunResult",
    "ShellRuntimeTelemetry",
]
