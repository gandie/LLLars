from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

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


__all__ = [
    "ErrorEnvelope",
    "JobSpec",
    "JobState",
    "JobStatus",
    "RunResult",
]
