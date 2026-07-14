from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock, Thread

from fastapi import FastAPI, HTTPException, status

from lllars_core.config import HarnessConfig
from lllars_core.job_store import InMemoryJobStore, InvalidTransitionError
from lllars_core.runtime_models import ErrorEnvelope, JobSpec, JobStatus
from lllars_core.runtime_runner import run_job


@dataclass
class RuntimeService:
    cfg: HarnessConfig
    store: InMemoryJobStore = field(default_factory=InMemoryJobStore)
    _threads: dict[str, Thread] = field(default_factory=dict)
    _threads_lock: Lock = field(default_factory=Lock)

    def submit(self, spec: JobSpec) -> JobStatus:
        record = self.store.create(spec)

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
            raise _not_found(job_id)
        return record.as_status()

    def cancel(self, job_id: str) -> JobStatus:
        record = self.store.get(job_id)
        if record is None:
            raise _not_found(job_id)
        return self.store.cancel(job_id).as_status()

    def logs(self, job_id: str) -> dict[str, object]:
        record = self.store.get(job_id)
        if record is None:
            raise _not_found(job_id)

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
            result = run_job(spec, cfg=self.cfg, show_progress=False)
            final_state = "succeeded" if result.success else "failed"
            failure_error = (
                None
                if result.success
                else ErrorEnvelope(
                    code="run_failed",
                    message="Job execution failed",
                    details={"agent_returncode": result.agent_returncode},
                )
            )
            self.store.update(
                job_id,
                status=final_state,
                result=result,
                error=failure_error,
            )
        except InvalidTransitionError:
            pass
        except Exception as exc:
            try:
                self.store.update(
                    job_id,
                    status="failed",
                    error=ErrorEnvelope(
                        code="run_exception",
                        message="Job execution raised an exception",
                        details={"error": str(exc)},
                    ),
                )
            except InvalidTransitionError:
                pass
        finally:
            self._cleanup_thread(job_id)

    def _cleanup_thread(self, job_id: str) -> None:
        with self._threads_lock:
            self._threads.pop(job_id, None)


def _not_found(job_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorEnvelope(
            code="not_found",
            message=f"Unknown job_id: {job_id}",
        ).model_dump(),
    )


def create_runtime_app(cfg: HarnessConfig) -> FastAPI:
    app = FastAPI(
        title="LLLars Runtime API",
        version="0.1.0",
    )
    service = RuntimeService(cfg=cfg)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/jobs",
        response_model=JobStatus,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def submit(spec: JobSpec) -> JobStatus:
        return service.submit(spec)

    @app.get("/jobs/{job_id}", response_model=JobStatus)
    def get_status(job_id: str) -> JobStatus:
        return service.status(job_id)

    @app.get("/jobs/{job_id}/logs")
    def get_logs(job_id: str) -> dict[str, object]:
        return service.logs(job_id)

    @app.post("/jobs/{job_id}/cancel", response_model=JobStatus)
    def cancel(job_id: str) -> JobStatus:
        return service.cancel(job_id)

    return app


__all__ = ["create_runtime_app", "RuntimeService"]
