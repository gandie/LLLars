from __future__ import annotations

from datetime import datetime
from time import time

from fastapi import FastAPI, status

from lllars_core.config import HarnessConfig
from lllars_core.runtime.service import RuntimeService
from lllars_core.runtime.web import mount_runtime_frontend
from lllars_core.runtime.models import JobSpec, JobStatus, TriggerRequest


def _register_health_route(
    app: FastAPI,
) -> None:
    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "server_now": datetime.now().isoformat(timespec="seconds"),
            "server_epoch_ms": int(time() * 1000),
        }


def _register_job_routes(
    app: FastAPI,
    service: RuntimeService,
) -> None:

    @app.post(
        "/jobs",
        response_model=JobStatus,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def submit(spec: JobSpec) -> JobStatus:
        return service.submit(spec)

    @app.get("/jobs", response_model=list[JobStatus])
    def list_jobs() -> list[JobStatus]:
        return service.list()

    @app.get("/jobs/{job_id}", response_model=JobStatus)
    def get_status(job_id: str) -> JobStatus:
        return service.status(job_id)

    @app.get("/jobs/{job_id}/logs")
    def get_logs(job_id: str) -> dict[str, object]:
        return service.logs(job_id)

    @app.post("/jobs/{job_id}/cancel", response_model=JobStatus)
    def cancel(job_id: str) -> JobStatus:
        return service.cancel(job_id)

    _register_job_trigger_route(app, service)


def _register_job_trigger_route(
    app: FastAPI,
    service: RuntimeService,
) -> None:

    @app.post("/jobs/{job_id}/trigger", response_model=JobStatus)
    def trigger(job_id: str, request: TriggerRequest) -> JobStatus:
        return service.trigger(
            job_id,
            trigger_source=request.trigger_source,
            trigger_payload_ref=request.trigger_payload_ref,
        )


def register_runtime_routes(
    app: FastAPI,
    service: RuntimeService,
) -> None:
    _register_health_route(app)
    _register_job_routes(app, service)


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
