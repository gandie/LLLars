from __future__ import annotations

from fastapi import FastAPI, status

from lllars_core.config import HarnessConfig
from lllars_core.runtime.service import RuntimeService
from lllars_core.runtime.web import mount_runtime_frontend
from lllars_core.runtime.models import JobSpec, JobStatus


def register_runtime_routes(
    app: FastAPI,
    service: RuntimeService,
) -> None:
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


def create_runtime_app(cfg: HarnessConfig) -> FastAPI:
    app = FastAPI(
        title="LLLars Runtime API",
        version="0.1.0",
    )
    service = RuntimeService(cfg=cfg)
    mount_runtime_frontend(app)
    register_runtime_routes(app, service)
    return app


__all__ = ["create_runtime_app", "register_runtime_routes"]
