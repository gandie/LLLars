from __future__ import annotations

from datetime import datetime
from threading import RLock
from time import time
from typing import TYPE_CHECKING, Mapping
from uuid import uuid4

from lllars_core.job_store_record import (
    TERMINAL_STATES,
    InvalidTransitionError,
    JobNotFoundError,
    JobRecord,
    JobStoreError,
    clone_record,
    validate_payload,
    validate_transition,
)
from dataclasses import replace

_UNSET = object()


def _updated_record(
    *,
    current: JobRecord,
    status: JobState,
    result: RunResult | None,
    error: ErrorEnvelope | None,
    artifacts: Mapping[str, str] | None,
    trigger_source: TriggerSource | None,
    trigger_payload_ref: str | None | object,
) -> JobRecord:
    merged_artifacts = dict(current.artifacts)
    if artifacts:
        merged_artifacts.update(artifacts)

    return replace(
        current,
        status=status,
        result=result if result is not None else current.result,
        error=error if error is not None else current.error,
        artifacts=merged_artifacts,
        trigger_source=(
            current.trigger_source
            if trigger_source is None
            else trigger_source
        ),
        trigger_payload_ref=(
            current.trigger_payload_ref
            if trigger_payload_ref is _UNSET
            else trigger_payload_ref
        ),
        updated_at=time(),
    )


if TYPE_CHECKING:
    from lllars_core.runtime.models import (
        ErrorEnvelope,
        JobSpec,
        JobState,
        RunResult,
        TriggerSource,
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
        next_run_at: datetime | None = None,
    ) -> JobRecord:
        resolved_job_id = job_id or f"job-{uuid4().hex}"
        now = time()
        record = JobRecord(
            job_id=resolved_job_id,
            spec=spec,
            status="queued",
            created_at=now,
            updated_at=now,
            trigger_source=spec.trigger_source,
            trigger_payload_ref=spec.trigger_payload_ref,
            next_run_at=next_run_at,
        )
        with self._lock:
            if resolved_job_id in self._jobs:
                raise JobStoreError(f"Job already exists: {resolved_job_id}")
            self._jobs[resolved_job_id] = record
            return clone_record(record)

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            record = self._jobs.get(job_id)
            return None if record is None else clone_record(record)

    def list(self) -> list[JobRecord]:
        with self._lock:
            cloned: list[JobRecord] = []
            for record in self._jobs.values():
                cloned.append(clone_record(record))
            return cloned

    def update(
        self,
        job_id: str,
        *,
        status: JobState | None = None,
        result: RunResult | None = None,
        error: ErrorEnvelope | None = None,
        artifacts: Mapping[str, str] | None = None,
        trigger_source: TriggerSource | None = None,
        trigger_payload_ref: str | None | object = _UNSET,
    ) -> JobRecord:
        with self._lock:
            current = self._require_job(job_id)
            next_status = status or current.status

            if status is not None and status != current.status:
                validate_transition(current.status, status)
            validate_payload(next_status, result, error, current)
            updated = _updated_record(
                current=current,
                status=next_status,
                result=result,
                error=error,
                artifacts=artifacts,
                trigger_source=trigger_source,
                trigger_payload_ref=trigger_payload_ref,
            )
            self._jobs[job_id] = updated
            return clone_record(updated)

    def mark_running(
        self,
        job_id: str,
        *,
        started_at: datetime,
    ) -> JobRecord:
        with self._lock:
            current = self._require_job(job_id)
            validate_transition(current.status, "running")
            updated = replace(
                current,
                status="running",
                last_run_at=started_at,
                next_run_at=None,
                run_count=current.run_count + 1,
                updated_at=time(),
            )
            self._jobs[job_id] = updated
            return clone_record(updated)

    def reschedule_recurring(
        self,
        job_id: str,
        *,
        next_run_at: datetime,
    ) -> JobRecord:
        with self._lock:
            current = self._require_job(job_id)
            if current.status == "canceled":
                return clone_record(current)
            if current.spec.schedule is None:
                return clone_record(current)
            updated = replace(
                current,
                status="queued",
                result=None,
                error=None,
                next_run_at=next_run_at,
                updated_at=time(),
            )
            self._jobs[job_id] = updated
            return clone_record(updated)

    def cancel(
        self,
        job_id: str,
        *,
        reason: str = "Canceled by operator",
    ) -> JobRecord:
        from lllars_core.runtime.models import ErrorEnvelope

        with self._lock:
            current = self._require_job(job_id)
            if current.status in TERMINAL_STATES:
                return clone_record(current)

            updated = replace(
                current,
                status="canceled",
                error=ErrorEnvelope(code="canceled", message=reason),
                updated_at=time(),
            )
            self._jobs[job_id] = updated
            return clone_record(updated)

    def _require_job(self, job_id: str) -> JobRecord:
        record = self._jobs.get(job_id)
        if record is None:
            raise JobNotFoundError(f"Unknown job_id: {job_id}")
        return record


__all__ = [
    "InMemoryJobStore",
    "InvalidTransitionError",
    "JobNotFoundError",
    "JobRecord",
    "JobStoreError",
]
