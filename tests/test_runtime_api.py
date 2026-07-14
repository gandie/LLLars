from __future__ import annotations

import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from lllars_core.runtime_models import RunResult
from lllars_core.runtime_api import create_runtime_app


class RuntimeApiTests(unittest.TestCase):
    def test_submit_and_poll_until_terminal_state(self) -> None:
        cfg = SimpleNamespace()
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
                json={"prompt": "hello", "timeout_sec": 5},
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


if __name__ == "__main__":
    unittest.main()
