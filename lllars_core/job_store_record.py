from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from lllars_core.runtime.models import (
        ErrorEnvelope,
        JobSpec,
        JobStatus,
        RunResult,
    )
else:
    ErrorEnvelope = Any
    JobSpec = Any
    JobStatus = Any
    RunResult = Any

JobState = Literal["queued", "running", "succeeded", "failed", "canceled"]

TERMINAL_STATES = frozenset({"succeeded", "failed", "canceled"})
_ALLOWED_TRANSITIONS: dict[JobState, frozenset[JobState]] = {
    "queued": frozenset({"running", "canceled"}),
    "running": frozenset({"succeeded", "failed", "canceled"}),
    "succeeded": frozenset(),
    "failed": frozenset(),
    "canceled": frozenset(),
}


class JobStoreError(RuntimeError):
    """Base error for in-memory job store operations."""


class JobNotFoundError(JobStoreError):
    """Raised when a job id does not exist in the store."""


class InvalidTransitionError(JobStoreError):
    """Raised when a requested state transition is not valid."""


@dataclass(frozen=True, slots=True)
class JobRecord:
    job_id: str
    spec: JobSpec
    status: JobState
    created_at: float
    updated_at: float
    result: RunResult | None = None
    error: ErrorEnvelope | None = None
    artifacts: dict[str, str] = field(default_factory=dict)
    trigger_source: str = "submit"
    trigger_payload_ref: str | None = None
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    run_count: int = 0

    def as_status(self) -> JobStatus:
        from lllars_core.runtime.models import JobStatus

        return JobStatus(
            job_id=self.job_id,
            status=self.status,
            trigger_source=self.trigger_source,
            trigger_payload_ref=self.trigger_payload_ref,
            run_at=self.spec.run_at,
            schedule=self.spec.schedule,
            next_run_at=self.next_run_at,
            last_run_at=self.last_run_at,
            run_count=self.run_count,
            result=self.result,
            error=self.error,
        )


def validate_transition(current: JobState, requested: JobState) -> None:
    if requested not in _ALLOWED_TRANSITIONS[current]:
        raise InvalidTransitionError(
            f"Invalid job transition: {current} -> {requested}"
        )


def validate_payload(
    status: JobState,
    result: RunResult | None,
    error: ErrorEnvelope | None,
    current: JobRecord,
) -> None:
    effective_result = result if result is not None else current.result
    effective_error = error if error is not None else current.error

    if status == "succeeded" and effective_result is None:
        raise ValueError("status='succeeded' requires a RunResult")
    if status in {"queued", "running"} and effective_result is not None:
        raise ValueError("RunResult can only be set for terminal states")
    if (
        status in {"queued", "running", "succeeded"}
        and effective_error is not None
    ):
        raise ValueError(
            "ErrorEnvelope is only valid for failed/canceled jobs"
        )


def clone_record(record: JobRecord) -> JobRecord:
    return replace(
        record,
        spec=record.spec.model_copy(deep=True),
        result=(
            None
            if record.result is None
            else record.result.model_copy(deep=True)
        ),
        error=(
            None
            if record.error is None
            else record.error.model_copy(deep=True)
        ),
        artifacts=dict(record.artifacts),
    )


__all__ = [
    "InvalidTransitionError",
    "JobNotFoundError",
    "JobRecord",
    "JobStoreError",
    "TERMINAL_STATES",
    "clone_record",
    "validate_payload",
    "validate_transition",
]
