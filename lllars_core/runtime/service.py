from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock, Thread

from fastapi import HTTPException, status

from lllars_core.config import HarnessConfig
from lllars_core.job_store import InMemoryJobStore, InvalidTransitionError
from lllars_core.runtime.artifacts import persist_runtime_artifacts
from lllars_core.runtime.service_execution import (
    execute_job,
    handle_exception,
    handle_shell_unavailable,
)
from lllars_core.runtime.job_runner import (
    ShellAdapterUnavailableError,
    run_job,
)
from lllars_core.runtime.models import (
    ErrorEnvelope,
    JobSpec,
    JobStatus,
    RunResult,
)


@dataclass
class RuntimeService:
    cfg: HarnessConfig
    store: InMemoryJobStore = field(default_factory=InMemoryJobStore)
    _threads: dict[str, Thread] = field(default_factory=dict)
    _threads_lock: Lock = field(default_factory=Lock)
    _cancel_requests: set[str] = field(default_factory=set)
    _cancel_lock: Lock = field(default_factory=Lock)

    def submit(self, spec: JobSpec) -> JobStatus:
        record = self.store.create(spec)
        self._clear_cancel_request(record.job_id)

        thread = Thread(
            target=self._run_job,
            args=(record.job_id, spec),
            name=f"runtime-job-{record.job_id}",
            daemon=True,
        )
        with self._threads_lock:
            self._threads[record.job_id] = thread
        thread.start()
        return record.as_status()

    def status(self, job_id: str) -> JobStatus:
        record = self.store.get(job_id)
        if record is None:
            raise not_found(job_id)
        return record.as_status()

    def cancel(self, job_id: str) -> JobStatus:
        record = self.store.get(job_id)
        if record is None:
            raise not_found(job_id)
        self._mark_cancel_requested(job_id)
        return self.store.cancel(job_id).as_status()

    def logs(self, job_id: str) -> dict[str, object]:
        record = self.store.get(job_id)
        if record is None:
            raise not_found(job_id)

        result = record.result
        return {
            "job_id": record.job_id,
            "status": record.status,
            "agent_stdout": "" if result is None else result.agent_stdout,
            "agent_stderr": "" if result is None else result.agent_stderr,
            "thought_trace": [] if result is None else result.thought_trace,
        }

    def _run_job(self, job_id: str, spec: JobSpec) -> None:
        try:
            self.store.update(job_id, status="running")
        except InvalidTransitionError:
            self._cleanup_thread(job_id)
            return

        try:
            execute_job(
                self,
                job_id,
                spec,
                run_job_fn=run_job,
            )
        except InvalidTransitionError:
            pass
        except ShellAdapterUnavailableError as exc:
            handle_shell_unavailable(self, job_id, exc)
        except Exception as exc:
            handle_exception(self, job_id, exc)
        finally:
            self._cleanup_thread(job_id)
            self._clear_cancel_request(job_id)

    def _mark_cancel_requested(self, job_id: str) -> None:
        with self._cancel_lock:
            self._cancel_requests.add(job_id)

    def _is_cancel_requested(self, job_id: str) -> bool:
        with self._cancel_lock:
            return job_id in self._cancel_requests

    def _clear_cancel_request(self, job_id: str) -> None:
        with self._cancel_lock:
            self._cancel_requests.discard(job_id)

    def _persist_artifacts(
        self,
        *,
        job_id: str,
        status: str,
        result: RunResult | None,
        error: ErrorEnvelope | None,
    ) -> dict[str, str]:
        artifacts_root = getattr(self.cfg, "mount_artifacts_root", None)
        return persist_runtime_artifacts(
            artifacts_root=artifacts_root,
            job_id=job_id,
            status=status,
            result=result,
            error=error,
        )

    def _cleanup_thread(self, job_id: str) -> None:
        with self._threads_lock:
            self._threads.pop(job_id, None)


def not_found(job_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorEnvelope(
            code="not_found",
            message=f"Unknown job_id: {job_id}",
        ).model_dump(),
    )


__all__ = [
    "RuntimeService",
    "ShellAdapterUnavailableError",
    "not_found",
    "run_job",
]
