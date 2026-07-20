from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from lllars_core.runtime import RuntimeService as PackageRuntimeService
from lllars_core.runtime import (
    create_runtime_app as package_create_runtime_app,
)
from lllars_core.runtime.api import create_runtime_app
from lllars_core.runtime.service import RuntimeService

from runtime_api_test_support import make_runtime_client


class RuntimeApiSurfaceTests(unittest.TestCase):
    def test_runtime_package_exports_api_symbols(self) -> None:
        self.assertIs(package_create_runtime_app, create_runtime_app)
        self.assertIs(PackageRuntimeService, RuntimeService)

    def test_runtime_frontend_root_serves_html(self) -> None:
        client = make_runtime_client(model="", provider_url="")
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("LLLars Runtime Console", response.text)
        self.assertIn("succeeded", response.text)
        self.assertIn("failed", response.text)
        self.assertIn("canceled", response.text)

    def test_unknown_job_returns_not_found(self) -> None:
        cfg = SimpleNamespace()
        app = create_runtime_app(cfg)
        client = TestClient(app)
        self.assertEqual(client.get("/jobs/missing-job").status_code, 404)
        self.assertEqual(
            client.post("/jobs/missing-job/trigger", json={}).status_code,
            404,
        )
        self.assertEqual(
            client.post("/jobs/missing-job/cancel").status_code,
            404,
        )
        self.assertEqual(client.get("/jobs/missing-job/logs").status_code, 404)

    def test_jobs_list_endpoint_is_available(self) -> None:
        client = make_runtime_client()
        response = client.get("/jobs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_health_exposes_clock_sync_fields(self) -> None:
        client = make_runtime_client(model="", provider_url="")
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("server_now", payload)
        self.assertIn("server_epoch_ms", payload)

    def test_runtime_frontend_fallback_when_static_missing(self) -> None:
        cfg = SimpleNamespace(model="", provider_url="")
        with patch(
            "lllars_core.runtime.web.RUNTIME_UI_DIR",
            Path("missing-ui"),
        ):
            app = create_runtime_app(cfg)
        client = TestClient(app)
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "ui": "unavailable"},
        )


if __name__ == "__main__":
    unittest.main()
