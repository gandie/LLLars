from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock, Thread

from lllars_core.config import HarnessConfig
from lllars_core.job_store import InMemoryJobStore, InvalidTransitionError
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
    TriggerSource,
)
from lllars_core.runtime.service_triggering import (
    not_found,
    persist_service_artifacts,
    trigger_job,
)
from lllars_core.runtime.scheduler import (
    RuntimeScheduler,
    next_scheduled_time,
)


@dataclass
class RuntimeService:
    cfg: HarnessConfig
    store: InMemoryJobStore = field(default_factory=InMemoryJobStore)
    _threads: dict[str, Thread] = field(default_factory=dict)
    _threads_lock: Lock = field(default_factory=Lock)
    _cancel_requests: set[str] = field(default_factory=set)
    _cancel_lock: Lock = field(default_factory=Lock)
    _scheduler: RuntimeScheduler | None = None

    def __post_init__(self) -> None:
        self._scheduler = RuntimeScheduler(
            list_jobs=self.store.list,
            is_job_active=self._is_job_active,
            start_job=self._start_scheduled_job,
        )
        self._scheduler.start()

    def submit(self, spec: JobSpec) -> JobStatus:
        next_run_at = self._initial_next_run_at(spec)
        record = self.store.create(spec, next_run_at=next_run_at)
        self._clear_cancel_request(record.job_id)
        if self._should_start_immediately(spec):
            self._start_job_thread(record.job_id)

        return record.as_status()

    def list(self) -> list[JobStatus]:
        return [record.as_status() for record in self.store.list()]

    @staticmethod
    def _should_start_immediately(spec: JobSpec) -> bool:
        return spec.run_at is None and spec.schedule is None

    def _initial_next_run_at(self, spec: JobSpec) -> datetime | None:
        if spec.run_at is not None:
            return spec.run_at
        if spec.schedule is not None:
            return next_scheduled_time(spec.schedule, now=datetime.now())
        return None

    def _start_job_thread(self, job_id: str) -> None:
        record = self.store.get(job_id)
        if record is None:
            return

        thread = Thread(
            target=self._run_job,
            args=(job_id, record.spec),
            name=f"runtime-job-{job_id}",
            daemon=True,
        )
        with self._threads_lock:
            self._threads[job_id] = thread
        thread.start()

    def _start_scheduled_job(self, job_id: str) -> None:
        try:
            trigger_job(
                self,
                job_id,
                trigger_source="scheduled",
                trigger_payload_ref=None,
                raise_on_invalid=False,
            )
        except InvalidTransitionError:
            return

    def _is_job_active(self, job_id: str) -> bool:
        with self._threads_lock:
            thread = self._threads.get(job_id)
            return thread is not None and thread.is_alive()

    def status(self, job_id: str) -> JobStatus:
        record = self.store.get(job_id)
        if record is None:
            raise not_found(job_id)
        return record.as_status()

    def trigger(
        self,
        job_id: str,
        *,
        trigger_source: TriggerSource = "manual",
        trigger_payload_ref: str | None = None,
    ) -> JobStatus:
        return trigger_job(
            self,
            job_id,
            trigger_source=trigger_source,
            trigger_payload_ref=trigger_payload_ref,
            raise_on_invalid=True,
        )

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
            self.store.mark_running(job_id, started_at=datetime.now())
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
            self._reschedule_if_recurring(job_id, spec)
            self._cleanup_thread(job_id)
            self._clear_cancel_request(job_id)

    def _reschedule_if_recurring(self, job_id: str, spec: JobSpec) -> None:
        if spec.schedule is None:
            return
        next_run_at = next_scheduled_time(spec.schedule, now=datetime.now())
        self.store.reschedule_recurring(job_id, next_run_at=next_run_at)

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
        return persist_service_artifacts(
            self,
            job_id=job_id,
            status=status,
            result=result,
            error=error,
        )

    def _cleanup_thread(self, job_id: str) -> None:
        with self._threads_lock:
            self._threads.pop(job_id, None)


__all__ = [
    "RuntimeService",
    "ShellAdapterUnavailableError",
    "not_found",
    "run_job",
]
