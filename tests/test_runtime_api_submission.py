from __future__ import annotations

from datetime import datetime, timedelta
import time
import unittest
from unittest.mock import patch

from lllars_core.runtime.models import RunResult

from runtime_api_test_support import (
    extended_run_payload,
    make_runtime_client,
    submit_job,
    wait_for_status,
    wait_for_terminal_status,
)


class RuntimeApiSubmissionTests(unittest.TestCase):
    def _wait_for_requeued_cycle(
        self,
        client,
        job_id: str,
    ) -> dict[str, object]:
        payload: dict[str, object] = {}
        for _ in range(200):
            payload = client.get(f"/jobs/{job_id}").json()
            if (
                payload.get("status") == "queued"
                and int(payload.get("run_count", 0)) >= 1
            ):
                return payload
            time.sleep(0.05)
        return payload

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
                    "config_path": "playground.example.json",
                    "deadline_at": "2030-01-01T00:00:00",
                    "trigger_source": "external",
                    "trigger_payload_ref": "event-42",
                },
            )
        self.assertEqual(submit_resp.status_code, 202)
        payload = submit_resp.json()
        self.assertEqual(payload["trigger_source"], "external")
        self.assertEqual(payload["trigger_payload_ref"], "event-42")

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

    def test_submit_rejects_invalid_schedule_grammar(self) -> None:
        client = make_runtime_client()
        submit_resp = client.post(
            "/jobs",
            json={
                "prompt": "hello",
                "run": extended_run_payload(),
                "timeout_sec": 5,
                "schedule": "cron:* * * * *",
                "trigger_source": "scheduled",
            },
        )
        self.assertEqual(submit_resp.status_code, 422)

    def test_submit_with_run_at_executes_after_scheduler_promotion(
        self,
    ) -> None:
        client = make_runtime_client()
        run_at = datetime.now() + timedelta(seconds=1)

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
            job_id = submit_job(
                client,
                spec_overrides={"run_at": run_at.isoformat()},
            )
            queued_payload = wait_for_status(
                client,
                job_id,
                statuses={"queued"},
            )
            status_payload = wait_for_terminal_status(client, job_id)

        self.assertEqual(queued_payload["status"], "queued")
        self.assertEqual(queued_payload["run_at"], run_at.isoformat())
        self.assertEqual(status_payload["status"], "succeeded")

    def test_submit_with_schedule_requeues_and_increments_run_count(
        self,
    ) -> None:
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
            job_id = submit_job(
                client,
                spec_overrides={
                    "schedule": "every:1s",
                    "trigger_source": "scheduled",
                },
            )
            steady_payload = self._wait_for_requeued_cycle(client, job_id)

        self.assertEqual(steady_payload["status"], "queued")
        self.assertEqual(steady_payload["schedule"], "every:1s")
        self.assertGreaterEqual(steady_payload["run_count"], 1)
        self.assertIsNotNone(steady_payload["next_run_at"])

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
