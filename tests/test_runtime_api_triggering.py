from __future__ import annotations

from datetime import datetime, timedelta
import unittest
from unittest.mock import patch

from lllars_core.runtime.models import RunResult

from runtime_api_test_support import (
    extended_run_payload,
    make_runtime_client,
    submit_job,
    wait_for_terminal_status,
)


class RuntimeApiTriggeringTests(unittest.TestCase):
    def test_submit_sets_default_trigger_metadata(self) -> None:
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
                },
            )

        payload = submit_resp.json()
        self.assertEqual(submit_resp.status_code, 202)
        self.assertEqual(payload["trigger_source"], "submit")
        self.assertIsNone(payload["trigger_payload_ref"])

    def test_trigger_route_defaults_to_manual_metadata(self) -> None:
        trigger_resp, status_payload = self._trigger_scheduled_job(json={})
        self.assertEqual(trigger_resp.status_code, 200)
        payload = trigger_resp.json()
        self.assertEqual(payload["trigger_source"], "manual")
        self.assertIsNone(payload["trigger_payload_ref"])
        self.assertEqual(status_payload["status"], "succeeded")
        self.assertEqual(status_payload["trigger_source"], "manual")
        self.assertIsNone(status_payload["trigger_payload_ref"])

    def test_trigger_route_accepts_explicit_metadata(self) -> None:
        trigger_resp, status_payload = self._trigger_scheduled_job(
            json={
                "trigger_source": "external",
                "trigger_payload_ref": "event-42",
            }
        )
        self.assertEqual(trigger_resp.status_code, 200)
        payload = trigger_resp.json()
        self.assertEqual(payload["trigger_source"], "external")
        self.assertEqual(payload["trigger_payload_ref"], "event-42")
        self.assertEqual(status_payload["status"], "succeeded")
        self.assertEqual(status_payload["trigger_source"], "external")
        self.assertEqual(status_payload["trigger_payload_ref"], "event-42")

    def _trigger_scheduled_job(self, *, json: dict[str, object]):
        client = make_runtime_client()
        run_at = datetime.now() + timedelta(seconds=90)
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
                    "run_at": run_at.isoformat(),
                    "trigger_source": "scheduled",
                },
            )
            trigger_resp = client.post(f"/jobs/{job_id}/trigger", json=json)
            status_payload = wait_for_terminal_status(client, job_id)
        return trigger_resp, status_payload


if __name__ == "__main__":
    unittest.main()
