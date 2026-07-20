from __future__ import annotations

from fastapi import HTTPException, status

from lllars_core.job_store import InvalidTransitionError
from lllars_core.runtime.artifacts import persist_runtime_artifacts
from lllars_core.runtime.models import ErrorEnvelope, JobStatus, TriggerSource


def trigger_job(
    service: object,
    job_id: str,
    *,
    trigger_source: TriggerSource,
    trigger_payload_ref: str | None,
    raise_on_invalid: bool,
) -> JobStatus:
    store = service.store
    record = store.get(job_id)
    if record is None:
        if raise_on_invalid:
            raise not_found(job_id)
        raise InvalidTransitionError(f"Unknown job_id: {job_id}")

    if record.status != "queued":
        if raise_on_invalid:
            raise _invalid_state(record.status)
        raise InvalidTransitionError(
            f"Only queued jobs can be triggered: {record.status}"
        )

    updated = store.update(
        job_id,
        trigger_source=trigger_source,
        trigger_payload_ref=trigger_payload_ref,
    )
    service._clear_cancel_request(job_id)
    service._start_job_thread(job_id)
    return updated.as_status()


def trigger_metadata(
    service: object,
    job_id: str,
) -> tuple[str, str | None]:
    record = service.store.get(job_id)
    if record is None:
        return "submit", None
    return record.trigger_source, record.trigger_payload_ref


def persist_service_artifacts(
    service: object,
    *,
    job_id: str,
    status: str,
    result: object,
    error: object,
) -> dict[str, str]:
    artifacts_root = getattr(service.cfg, "mount_artifacts_root", None)
    trigger_source, trigger_payload_ref = trigger_metadata(service, job_id)
    return persist_runtime_artifacts(
        artifacts_root=artifacts_root,
        job_id=job_id,
        status=status,
        result=result,
        error=error,
        trigger_source=trigger_source,
        trigger_payload_ref=trigger_payload_ref,
    )


def _invalid_state(current_status: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=ErrorEnvelope(
            code="invalid_state",
            message="Only queued jobs can be triggered",
            details={"status": current_status},
        ).model_dump(),
    )


def not_found(job_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorEnvelope(
            code="not_found",
            message=f"Unknown job_id: {job_id}",
        ).model_dump(),
    )


__all__ = [
    "not_found",
    "persist_service_artifacts",
    "trigger_job",
    "trigger_metadata",
]
