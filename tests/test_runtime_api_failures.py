from __future__ import annotations

import time
import unittest
from threading import Event
from unittest.mock import patch

from lllars_core.runtime.job_runner import ShellAdapterUnavailableError
from lllars_core.runtime.models import RunResult

from runtime_api_test_support import (
    make_runtime_client,
    submit_job,
    wait_for_terminal_status,
)


def _blocking_cancelable_run_job(*args, **kwargs) -> RunResult:
    _ = args
    cancel_requested = kwargs.get("cancel_requested")
    started = kwargs.get("started")
    if started is not None:
        started.set()
    for _ in range(200):
        if cancel_requested is not None and cancel_requested():
            return RunResult(
                success=False,
                agent_returncode=130,
                elapsed_sec=0.01,
                agent_stdout="",
                agent_stderr="[lllars] agent canceled",
            )
        time.sleep(0.01)
    return RunResult(
        success=True,
        agent_returncode=0,
        elapsed_sec=0.01,
        agent_stdout="late-success",
        agent_stderr="",
    )


class RuntimeApiFailureTests(unittest.TestCase):
    def test_cancel_force_terminates_inflight_job(self) -> None:
        client = make_runtime_client()
        started = Event()

        def side_effect(*args, **kwargs):
            kwargs["started"] = started
            return _blocking_cancelable_run_job(*args, **kwargs)

        with patch(
            "lllars_core.runtime.service.run_job",
            side_effect=side_effect,
        ):
            job_id = submit_job(client)
            self.assertTrue(started.wait(timeout=1.0))
            cancel_resp = client.post(f"/jobs/{job_id}/cancel")
            self.assertEqual(cancel_resp.status_code, 200)
            self.assertEqual(cancel_resp.json()["status"], "canceled")
            status_payload = wait_for_terminal_status(client, job_id)

        self.assertEqual(status_payload["status"], "canceled")
        self.assertIsNone(status_payload["result"])
        self.assertEqual(status_payload["error"]["code"], "canceled")

    def test_submit_surfaces_shell_unavailable_envelope(self) -> None:
        client = make_runtime_client()
        with patch(
            "lllars_core.runtime.service.run_job",
            side_effect=ShellAdapterUnavailableError(
                shell_mode="auto",
                shell_override=None,
            ),
        ):
            job_id = submit_job(client)
            status_payload = wait_for_terminal_status(client, job_id)

        self.assertEqual(status_payload["status"], "failed")
        error_payload = status_payload["error"]
        self.assertEqual(error_payload["code"], "shell_unavailable")
        self.assertEqual(
            error_payload["details"],
            {"shell_mode": "auto", "shell_override": None},
        )

    def test_run_failed_error_includes_shell_metadata(self) -> None:
        client = make_runtime_client()
        with patch(
            "lllars_core.runtime.service.run_job",
            return_value=RunResult(
                success=False,
                agent_returncode=1,
                elapsed_sec=0.01,
                agent_stdout="",
                agent_stderr="boom",
                runtime_telemetry={
                    "shell": {
                        "selected": "powershell",
                        "shell_mode": "auto",
                        "shell_override": None,
                        "invocation_mode": "auto_detect",
                    }
                },
                eval_error="eval failed",
            ),
        ):
            job_id = submit_job(client)
            status_payload = wait_for_terminal_status(client, job_id)

        self.assertEqual(status_payload["status"], "failed")
        error_payload = status_payload["error"]
        self.assertEqual(error_payload["code"], "run_failed")
        self.assertEqual(error_payload["details"]["agent_returncode"], 1)
        self.assertEqual(error_payload["details"]["eval_error"], "eval failed")
        self.assertIn("shell", error_payload["details"])


if __name__ == "__main__":
    unittest.main()
