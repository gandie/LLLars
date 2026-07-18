from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


RUNTIME_UI_DIR = Path(__file__).resolve().parents[1] / "static" / "runtime"


def mount_runtime_frontend(app: FastAPI) -> None:
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


__all__ = ["RUNTIME_UI_DIR", "mount_runtime_frontend"]
