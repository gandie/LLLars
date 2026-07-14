from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from lllars_core.runtime_models import JobSpec, RunResult
from lllars_core.runtime_api import RuntimeService, create_runtime_app


class RuntimeApiTests(unittest.TestCase):
    def test_submit_rejects_missing_run_fields_in_request(
        self,
    ) -> None:
        cfg = SimpleNamespace(model="", provider_url="")
        app = create_runtime_app(cfg)
        client = TestClient(app)

        submit_resp = client.post(
            "/jobs",
            json={"prompt": "hello", "timeout_sec": 5},
        )

        self.assertEqual(submit_resp.status_code, 422)

    def test_submit_and_poll_until_terminal_state(self) -> None:
        cfg = SimpleNamespace(
            model="test-model",
            provider_url="http://localhost:11434",
        )
        app = create_runtime_app(cfg)
        client = TestClient(app)

        with patch(
            "lllars_core.runtime_api.run_job",
            return_value=RunResult(
                success=True,
                agent_returncode=0,
                elapsed_sec=0.01,
                agent_stdout="agent-out",
                agent_stderr="",
                thought_trace=["trace-1"],
            ),
        ):
            submit_resp = client.post(
                "/jobs",
                json={
                    "prompt": "hello",
                    "run": {
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": ".",
                        "command_profile": "none",
                    },
                    "timeout_sec": 5,
                },
            )

            self.assertEqual(submit_resp.status_code, 202)
            job_id = submit_resp.json()["job_id"]

            status_payload: dict[str, object] = {}
            for _ in range(60):
                status_resp = client.get(f"/jobs/{job_id}")
                self.assertEqual(status_resp.status_code, 200)
                status_payload = status_resp.json()
                if status_payload["status"] in {
                    "succeeded",
                    "failed",
                    "canceled",
                }:
                    break
                time.sleep(0.05)

            self.assertEqual(status_payload["status"], "succeeded")

            logs_resp = client.get(f"/jobs/{job_id}/logs")
            self.assertEqual(logs_resp.status_code, 200)
            logs_payload = logs_resp.json()
            self.assertEqual(logs_payload["agent_stdout"], "agent-out")
            self.assertEqual(logs_payload["thought_trace"], ["trace-1"])

    def test_unknown_job_returns_not_found(self) -> None:
        cfg = SimpleNamespace()
        app = create_runtime_app(cfg)
        client = TestClient(app)

        status_resp = client.get("/jobs/missing-job")
        self.assertEqual(status_resp.status_code, 404)

        cancel_resp = client.post("/jobs/missing-job/cancel")
        self.assertEqual(cancel_resp.status_code, 404)

        logs_resp = client.get("/jobs/missing-job/logs")
        self.assertEqual(logs_resp.status_code, 404)

    def test_runtime_service_persists_artifacts_on_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = SimpleNamespace(mount_artifacts_root=Path(tmpdir))
            service = RuntimeService(cfg=cfg)
            spec = service.store.create(
                JobSpec(
                    prompt="hello",
                    run={
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": ".",
                        "command_profile": "none",
                    },
                    timeout_sec=5,
                ),
                job_id="job-success",
            ).spec

            with patch(
                "lllars_core.runtime_api.run_job",
                return_value=RunResult(
                    success=True,
                    agent_returncode=0,
                    elapsed_sec=0.01,
                    agent_stdout="agent-out",
                    agent_stderr="",
                    thought_trace=["trace-1"],
                    runtime_telemetry={"timeline": [{"event": "done"}]},
                ),
            ):
                service._run_job("job-success", spec)

            record = service.store.get("job-success")
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(record.status, "succeeded")

            summary_rel = record.artifacts["summary"]
            stdout_rel = record.artifacts["stdout"]
            telemetry_rel = record.artifacts["telemetry"]
            summary_path = Path(tmpdir) / summary_rel
            stdout_path = Path(tmpdir) / stdout_rel
            telemetry_path = Path(tmpdir) / telemetry_rel

            self.assertTrue(summary_path.exists())
            self.assertTrue(stdout_path.exists())
            self.assertTrue(telemetry_path.exists())
            self.assertEqual(
                stdout_path.read_text(encoding="utf-8"),
                "agent-out",
            )

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["job_id"], "job-success")
            self.assertEqual(summary["status"], "succeeded")

    def test_runtime_service_persists_artifacts_on_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = SimpleNamespace(mount_artifacts_root=Path(tmpdir))
            service = RuntimeService(cfg=cfg)
            spec = service.store.create(
                JobSpec(
                    prompt="hello",
                    run={
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": ".",
                        "command_profile": "none",
                    },
                    timeout_sec=5,
                ),
                job_id="job-failure",
            ).spec

            with patch(
                "lllars_core.runtime_api.run_job",
                side_effect=RuntimeError("boom"),
            ):
                service._run_job("job-failure", spec)

            record = service.store.get("job-failure")
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(record.status, "failed")
            self.assertIn("summary", record.artifacts)
            self.assertIn("stderr", record.artifacts)

            summary_path = Path(tmpdir) / record.artifacts["summary"]
            stderr_path = Path(tmpdir) / record.artifacts["stderr"]
            self.assertTrue(summary_path.exists())
            self.assertTrue(stderr_path.exists())

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "failed")
            self.assertEqual(summary["error"]["code"], "run_exception")


if __name__ == "__main__":
    unittest.main()
