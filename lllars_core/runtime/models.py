from __future__ import annotations

from typing import Any, Literal
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator
from lllars_core.config import RunConfig
from lllars_core.runtime.override_fields import (
    HARNESS_RUN_SYNC_FIELDS,
    RUN_CFG_OVERRIDE_FIELDS,
)
from lllars_core.runtime.scheduler import parse_interval_schedule


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


JobState = Literal["queued", "running", "succeeded", "failed", "canceled"]
TriggerSource = Literal[
    "submit", "scheduled", "manual", "api", "retry", "external"
]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JobSpec(_StrictModel):
    prompt: str = Field(min_length=1)
    run: RunConfig
    timeout_sec: int = Field(default=600, gt=0)
    config_path: str | None = None
    deadline_at: datetime | None = Field(
        default=None,
        description=(
            "Latest acceptable completion/start boundary "
            "for strategy scheduling."
        ),
    )
    run_at: datetime | None = Field(
        default=None,
        description="One-shot planned execution time.",
    )
    schedule: str | None = Field(
        default=None,
        min_length=1,
        description=(
            "Opaque schedule strategy selector or expression "
            "(for example, carbon-aware)."
        ),
    )
    trigger_source: TriggerSource = "submit"
    trigger_payload_ref: str | None = None

    @model_validator(mode="after")
    def validate_datetime_contract(self) -> JobSpec:
        if (
            self.deadline_at is not None
            and self.deadline_at.tzinfo is not None
        ):
            raise ValueError("deadline_at must be timezone-naive")

        if self.run_at is not None and self.run_at.tzinfo is not None:
            raise ValueError("run_at must be timezone-naive")

        if (
            self.deadline_at is not None
            and self.run_at is not None
            and self.run_at > self.deadline_at
        ):
            raise ValueError(
                "run_at must be less than or equal to deadline_at"
            )

        return self

    @model_validator(mode="after")
    def validate_schedule_contract(self) -> JobSpec:
        if self.schedule is not None and self.run_at is not None:
            raise ValueError("run_at and schedule are mutually exclusive")

        if self.schedule is not None:
            parse_interval_schedule(self.schedule)

        if self.schedule is not None and self.trigger_source != "scheduled":
            raise ValueError(
                "trigger_source must be 'scheduled' when schedule is provided"
            )

        if (
            self.trigger_source == "scheduled"
            and self.schedule is None
            and self.run_at is None
        ):
            raise ValueError(
                "scheduled trigger_source requires schedule or run_at"
            )

        return self


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


class TriggerRequest(_StrictModel):
    trigger_source: TriggerSource = "manual"
    trigger_payload_ref: str | None = None


class JobStatus(_StrictModel):
    job_id: str = Field(min_length=1)
    status: JobState
    trigger_source: TriggerSource = "submit"
    trigger_payload_ref: str | None = None
    run_at: datetime | None = None
    schedule: str | None = None
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    run_count: int = Field(default=0, ge=0)
    result: RunResult | None = None
    error: ErrorEnvelope | None = None


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
    "TriggerRequest",
    "TriggerSource",
]
