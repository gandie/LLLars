from __future__ import annotations

from dataclasses import dataclass, field, replace
from threading import RLock
from time import time
from typing import Mapping
from uuid import uuid4

from lllars_core.runtime.models import (
    ErrorEnvelope,
    JobSpec,
    JobState,
    JobStatus,
    RunResult,
)

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

    def as_status(self) -> JobStatus:
        return JobStatus(
            job_id=self.job_id,
            status=self.status,
            result=self.result,
            error=self.error,
        )


class InMemoryJobStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._jobs: dict[str, JobRecord] = {}

    def create(
        self,
        spec: JobSpec,
        *,
        job_id: str | None = None,
    ) -> JobRecord:
        resolved_job_id = job_id or f"job-{uuid4().hex}"
        now = time()
        record = JobRecord(
            job_id=resolved_job_id,
            spec=spec,
            status="queued",
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            if resolved_job_id in self._jobs:
                raise JobStoreError(f"Job already exists: {resolved_job_id}")
            self._jobs[resolved_job_id] = record
            return self._clone_record(record)

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            record = self._jobs.get(job_id)
            return None if record is None else self._clone_record(record)

    def list(self) -> list[JobRecord]:
        with self._lock:
            return [
                self._clone_record(record)
                for record in self._jobs.values()
            ]

    def update(
        self,
        job_id: str,
        *,
        status: JobState | None = None,
        result: RunResult | None = None,
        error: ErrorEnvelope | None = None,
        artifacts: Mapping[str, str] | None = None,
    ) -> JobRecord:
        with self._lock:
            current = self._require_job(job_id)
            next_status = status or current.status

            if status is not None and status != current.status:
                self._validate_transition(current.status, status)

            self._validate_payload(next_status, result, error, current)

            merged_artifacts = dict(current.artifacts)
            if artifacts:
                merged_artifacts.update(artifacts)

            updated = replace(
                current,
                status=next_status,
                result=result if result is not None else current.result,
                error=error if error is not None else current.error,
                artifacts=merged_artifacts,
                updated_at=time(),
            )
            self._jobs[job_id] = updated
            return self._clone_record(updated)

    def cancel(
        self,
        job_id: str,
        *,
        reason: str = "Canceled by operator",
    ) -> JobRecord:
        with self._lock:
            current = self._require_job(job_id)
            if current.status in TERMINAL_STATES:
                return self._clone_record(current)

            updated = replace(
                current,
                status="canceled",
                error=ErrorEnvelope(code="canceled", message=reason),
                updated_at=time(),
            )
            self._jobs[job_id] = updated
            return self._clone_record(updated)

    def _require_job(self, job_id: str) -> JobRecord:
        record = self._jobs.get(job_id)
        if record is None:
            raise JobNotFoundError(f"Unknown job_id: {job_id}")
        return record

    @staticmethod
    def _validate_transition(current: JobState, requested: JobState) -> None:
        if requested not in _ALLOWED_TRANSITIONS[current]:
            raise InvalidTransitionError(
                f"Invalid job transition: {current} -> {requested}"
            )

    @staticmethod
    def _validate_payload(
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

    @staticmethod
    def _clone_record(record: JobRecord) -> JobRecord:
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
    "InMemoryJobStore",
    "InvalidTransitionError",
    "JobNotFoundError",
    "JobRecord",
    "JobStoreError",
]
