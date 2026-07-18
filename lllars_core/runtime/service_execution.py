from __future__ import annotations

from typing import TYPE_CHECKING

from lllars_core.job_store import InvalidTransitionError
from lllars_core.runtime.job_runner import ShellAdapterUnavailableError
from lllars_core.runtime.models import ErrorEnvelope, JobSpec, RunResult

if TYPE_CHECKING:
    from lllars_core.runtime.service import RuntimeService


def execute_job(
    service: RuntimeService,
    job_id: str,
    spec: JobSpec,
    *,
    run_job_fn,
) -> None:
    result = run_job_fn(
        spec,
        cfg=service.cfg,
        show_progress=False,
        cancel_requested=lambda: service._is_cancel_requested(job_id),
    )
    _store_result(service, job_id, result)


def _store_result(
    service: RuntimeService,
    job_id: str,
    result: RunResult,
) -> None:
    final_state = _resolve_final_state(service, job_id, result)
    failure_error = _failure_error_for_result(final_state, result)
    service.store.update(
        job_id,
        status=final_state,
        result=None if final_state == "canceled" else result,
        error=failure_error,
        artifacts=service._persist_artifacts(
            job_id=job_id,
            status=final_state,
            result=result,
            error=failure_error,
        ),
    )


def _resolve_final_state(
    service: RuntimeService,
    job_id: str,
    result: RunResult,
) -> str:
    record = service.store.get(job_id)
    is_canceled = (
        record is not None and record.status == "canceled"
    ) or service._is_cancel_requested(job_id)
    if is_canceled:
        return "canceled"
    return "succeeded" if result.success else "failed"


def _failure_error_for_result(
    final_state: str,
    result: RunResult,
) -> ErrorEnvelope | None:
    if final_state != "failed":
        return None

    shell_details = result.runtime_telemetry.get("shell")
    details: dict[str, object] = {"agent_returncode": result.agent_returncode}
    if isinstance(shell_details, dict):
        details["shell"] = shell_details
    if result.eval_error:
        details["eval_error"] = result.eval_error

    return ErrorEnvelope(
        code="run_failed",
        message="Job execution failed",
        details=details,
    )


def handle_shell_unavailable(
    service: RuntimeService,
    job_id: str,
    exc: ShellAdapterUnavailableError,
) -> None:
    record = service.store.get(job_id)
    if record is not None and record.status == "canceled":
        store_canceled(service, job_id, record.error)
        return

    store_failed(
        service,
        job_id,
        ErrorEnvelope(
            code="shell_unavailable",
            message="No supported shell executable found",
            details={
                "shell_mode": exc.shell_mode,
                "shell_override": exc.shell_override,
            },
        ),
    )


def handle_exception(
    service: RuntimeService,
    job_id: str,
    exc: Exception,
) -> None:
    record = service.store.get(job_id)
    if record is not None and record.status == "canceled":
        store_canceled(service, job_id, record.error)
        return

    store_failed(
        service,
        job_id,
        ErrorEnvelope(
            code="run_exception",
            message="Job execution raised an exception",
            details={"error": str(exc)},
        ),
    )


def store_canceled(
    service: RuntimeService,
    job_id: str,
    error: ErrorEnvelope | None,
) -> None:
    _store_terminal_state(service, job_id, "canceled", error)


def store_failed(
    service: RuntimeService,
    job_id: str,
    error: ErrorEnvelope,
) -> None:
    _store_terminal_state(service, job_id, "failed", error)


def _store_terminal_state(
    service: RuntimeService,
    job_id: str,
    status: str,
    error: ErrorEnvelope | None,
) -> None:
    try:
        service.store.update(
            job_id,
            status=status,
            error=error,
            artifacts=service._persist_artifacts(
                job_id=job_id,
                status=status,
                result=None,
                error=error,
            ),
        )
    except InvalidTransitionError:
        pass


__all__ = [
    "execute_job",
    "handle_exception",
    "handle_shell_unavailable",
]
