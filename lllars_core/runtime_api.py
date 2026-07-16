from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock, Thread

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from lllars_core.config import HarnessConfig
from lllars_core.job_store import InMemoryJobStore, InvalidTransitionError
from lllars_core.runtime_artifacts import persist_job_artifacts
from lllars_core.runtime_models import (
    ErrorEnvelope,
    JobSpec,
    JobStatus,
    RunResult,
)
from lllars_core.runtime_runner import (
    ShellAdapterUnavailableError,
    run_job,
)


RUNTIME_UI_DIR = Path(__file__).resolve().parent / "static" / "runtime"


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
            shell_details = result.runtime_telemetry.get("shell")
            details: dict[str, object] = {
                "agent_returncode": result.agent_returncode
            }
            if isinstance(shell_details, dict):
                details["shell"] = shell_details
            if result.eval_error:
                details["eval_error"] = result.eval_error
            failure_error = (
                None
                if result.success
                else ErrorEnvelope(
                    code="run_failed",
                    message="Job execution failed",
                    details=details,
                )
            )
            artifacts = self._persist_artifacts(
                job_id=job_id,
                status=final_state,
                result=result,
                error=failure_error,
            )
            self.store.update(
                job_id,
                status=final_state,
                result=result,
                error=failure_error,
                artifacts=artifacts,
            )
        except InvalidTransitionError:
            pass
        except ShellAdapterUnavailableError as exc:
            failure_error = ErrorEnvelope(
                code="shell_unavailable",
                message="No supported shell executable found",
                details={
                    "shell_mode": exc.shell_mode,
                    "shell_override": exc.shell_override,
                },
            )
            artifacts = self._persist_artifacts(
                job_id=job_id,
                status="failed",
                result=None,
                error=failure_error,
            )
            try:
                self.store.update(
                    job_id,
                    status="failed",
                    error=failure_error,
                    artifacts=artifacts,
                )
            except InvalidTransitionError:
                pass
        except Exception as exc:
            failure_error = ErrorEnvelope(
                code="run_exception",
                message="Job execution raised an exception",
                details={"error": str(exc)},
            )
            artifacts = self._persist_artifacts(
                job_id=job_id,
                status="failed",
                result=None,
                error=failure_error,
            )
            try:
                self.store.update(
                    job_id,
                    status="failed",
                    error=failure_error,
                    artifacts=artifacts,
                )
            except InvalidTransitionError:
                pass
        finally:
            self._cleanup_thread(job_id)

    def _persist_artifacts(
        self,
        *,
        job_id: str,
        status: str,
        result: RunResult | None,
        error: ErrorEnvelope | None,
    ) -> dict[str, str]:
        artifacts_root = getattr(self.cfg, "mount_artifacts_root", None)
        if artifacts_root is None:
            return {}

        try:
            return persist_job_artifacts(
                artifacts_root=artifacts_root,
                job_id=job_id,
                status=status,
                result=result,
                error=error,
            )
        except Exception:
            return {}

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


def _mount_runtime_frontend(app: FastAPI) -> None:
    def runtime_ui_unavailable() -> dict[str, str]:
        return {"status": "ok", "ui": "unavailable"}

    index_path = RUNTIME_UI_DIR / "index.html"
    if not index_path.exists():
        app.add_api_route(
            "/",
            runtime_ui_unavailable,
            methods=["GET"],
            include_in_schema=False,
        )
        return

    try:
        app.mount(
            "/ui",
            StaticFiles(directory=str(RUNTIME_UI_DIR)),
            name="runtime-ui",
        )
    except Exception:
        app.add_api_route(
            "/",
            runtime_ui_unavailable,
            methods=["GET"],
            include_in_schema=False,
        )
        return

    @app.get("/", include_in_schema=False)
    def runtime_ui_index() -> FileResponse:
        return FileResponse(index_path)


def create_runtime_app(cfg: HarnessConfig) -> FastAPI:
    app = FastAPI(
        title="LLLars Runtime API",
        version="0.1.0",
    )
    service = RuntimeService(cfg=cfg)
    _mount_runtime_frontend(app)

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
