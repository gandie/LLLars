from __future__ import annotations

import unittest
from unittest.mock import patch

from lllars_core.runtime.models import RunResult

from runtime_api_test_support import (
    extended_run_payload,
    make_runtime_client,
    submit_job,
    wait_for_terminal_status,
)


class RuntimeApiSubmissionTests(unittest.TestCase):
    def test_submit_rejects_missing_run_fields_in_request(self) -> None:
        client = make_runtime_client(model="", provider_url="")
        submit_resp = client.post(
            "/jobs",
            json={"prompt": "hello", "timeout_sec": 5},
        )
        self.assertEqual(submit_resp.status_code, 422)

    def test_submit_accepts_extended_run_fields_in_request(self) -> None:
        client = make_runtime_client()
        with patch(
            "lllars_core.runtime.service.run_job",
            return_value=RunResult(
                success=True,
                agent_returncode=0,
                elapsed_sec=0.01,
                agent_stdout="agent-out",
                agent_stderr="",
            ),
        ):
            submit_resp = client.post(
                "/jobs",
                json={
                    "prompt": "hello",
                    "run": extended_run_payload(),
                    "timeout_sec": 5,
                    "deadline_at": "2030-01-01T00:00:00",
                },
            )
        self.assertEqual(submit_resp.status_code, 202)

    def test_submit_rejects_timezone_aware_deadline_field(self) -> None:
        client = make_runtime_client()
        submit_resp = client.post(
            "/jobs",
            json={
                "prompt": "hello",
                "run": extended_run_payload(),
                "timeout_sec": 5,
                "deadline_at": "2030-01-01T00:00:00+00:00",
            },
        )
        self.assertEqual(submit_resp.status_code, 422)

    def test_submit_and_poll_until_terminal_state(self) -> None:
        client = make_runtime_client()
        with patch(
            "lllars_core.runtime.service.run_job",
            return_value=RunResult(
                success=True,
                agent_returncode=0,
                elapsed_sec=0.01,
                agent_stdout="agent-out",
                agent_stderr="",
                thought_trace=["trace-1"],
            ),
        ):
            job_id = submit_job(client)
            status_payload = wait_for_terminal_status(client, job_id)

        self.assertEqual(status_payload["status"], "succeeded")
        logs_resp = client.get(f"/jobs/{job_id}/logs")
        self.assertEqual(logs_resp.status_code, 200)
        logs_payload = logs_resp.json()
        self.assertEqual(logs_payload["agent_stdout"], "agent-out")
        self.assertEqual(logs_payload["thought_trace"], ["trace-1"])


if __name__ == "__main__":
    unittest.main()
