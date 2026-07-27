from __future__ import annotations

from datetime import datetime
import unittest
from typing import Any

from runtime_api_smoke_test import run_smoke_test


def _run_smoke(
    *,
    request_json,
    now_fn=lambda: datetime(2030, 1, 1, 10, 0, 0),
    **overrides: Any,
) -> int:
    args: dict[str, Any] = {
        "base_url": "http://127.0.0.1:8000",
        "prompt": "hello",
        "model": "test-model",
        "provider_url": "http://localhost:11434",
        "project_root": ".",
        "command_profile": "playground-python",
        "test_command": "python test.py",
        "expected_shells": ("bash", "sh"),
        "poll_interval_sec": 0.001,
        "timeout_sec": 1.0,
        "request_json": request_json,
        "now_fn": now_fn,
    }
    args.update(overrides)
    return run_smoke_test(**args)


def _timed_request_json(submit_payloads: list[dict[str, object]]):
    def request_json(method: str, url: str, payload=None):
        if method == "GET" and url.endswith("/health"):
            return {"status": "ok"}
        if method == "POST" and url.endswith("/jobs"):
            submit_payloads.append(payload or {})
            return {"job_id": "job-1"}
        if method == "GET" and url.endswith("/jobs/job-1"):
            return {
                "status": "succeeded",
                "result": {
                    "test": {"returncode": 0},
                    "runtime_telemetry": {"shell": {"selected": "bash"}},
                },
            }
        if method == "GET" and url.endswith("/jobs/job-1/logs"):
            return {"agent_stdout": "", "agent_stderr": ""}
        raise AssertionError(f"Unexpected call: {method} {url}")

    return request_json


def _recurring_request_json():
    statuses = iter(
        [
            {"status": "running", "run_count": 1},
            {
                "status": "queued",
                "run_count": 1,
                "next_run_at": "2030-01-01T10:00:01",
            },
        ]
    )

    def request_json(method: str, url: str, payload=None):
        if method == "GET" and url.endswith("/health"):
            return {"status": "ok"}
        if method == "POST" and url.endswith("/jobs"):
            return {"job_id": "job-1"}
        if method == "GET" and url.endswith("/jobs/job-1"):
            return next(statuses)
        if method == "GET" and url.endswith("/jobs/job-1/logs"):
            return {"agent_stdout": "", "agent_stderr": ""}
        raise AssertionError(f"Unexpected call: {method} {url}")

    return request_json


def _trigger_request_json(trigger_payloads: list[dict[str, object]]):
    def request_json(method: str, url: str, payload=None):
        if method == "GET" and url.endswith("/health"):
            return {"status": "ok"}
        if method == "POST" and url.endswith("/jobs"):
            return {"job_id": "job-1"}
        if method == "POST" and url.endswith("/jobs/job-1/trigger"):
            trigger_payloads.append(payload or {})
            return {
                "job_id": "job-1",
                "status": "queued",
                "trigger_source": "manual",
                "trigger_payload_ref": "event-42",
            }
        if method == "GET" and url.endswith("/jobs/job-1"):
            return {
                "status": "succeeded",
                "trigger_source": "manual",
                "trigger_payload_ref": "event-42",
                "result": {
                    "test": {"returncode": 0},
                    "runtime_telemetry": {"shell": {"selected": "bash"}},
                },
            }
        if method == "GET" and url.endswith("/jobs/job-1/logs"):
            return {"agent_stdout": "", "agent_stderr": ""}
        raise AssertionError(f"Unexpected call: {method} {url}")

    return request_json


class RuntimeApiSmokeModeTests(unittest.TestCase):
    def test_timed_mode_submits_run_at_payload(self) -> None:
        submit_payloads: list[dict[str, object]] = []
        rc = _run_smoke(
            request_json=_timed_request_json(submit_payloads),
            run_mode="timed",
            run_at_delay_sec=30.0,
        )

        self.assertEqual(rc, 0)
        self.assertEqual(submit_payloads[0].get("run_at"), "2030-01-01T10:00:30")

    def test_recurring_mode_succeeds_on_requeue_cycle(self) -> None:
        rc = _run_smoke(
            request_json=_recurring_request_json(),
            run_mode="recurring",
            schedule="every:1s",
        )

        self.assertEqual(rc, 0)

    def test_trigger_mode_posts_trigger_payload(self) -> None:
        trigger_payloads: list[dict[str, object]] = []
        rc = _run_smoke(
            request_json=_trigger_request_json(trigger_payloads),
            run_mode="trigger",
            run_at_delay_sec=90.0,
            trigger_source="manual",
            trigger_payload_ref="event-42",
        )

        self.assertEqual(rc, 0)
        self.assertEqual(
            trigger_payloads,
            [{"trigger_source": "manual", "trigger_payload_ref": "event-42"}],
        )


if __name__ == "__main__":
    unittest.main()
