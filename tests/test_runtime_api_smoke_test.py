from __future__ import annotations

import unittest
from unittest.mock import patch

from runtime_api_smoke_test import run_smoke_test


class RuntimeApiSmokeScriptTests(unittest.TestCase):
    def test_run_smoke_test_returns_zero_on_succeeded_terminal_state(
        self,
    ) -> None:
        responses = [
            {"status": "ok"},
            {"job_id": "job-1"},
            {"status": "running"},
            {
                "status": "succeeded",
                "result": {
                    "test": {"returncode": 0},
                    "runtime_telemetry": {
                        "shell": {"selected": "bash"}
                    },
                },
            },
            {"agent_stdout": "done"},
        ]

        with (
            patch(
                "runtime_api_smoke_test._request_json",
                side_effect=responses,
            ) as request_json,
            patch(
                "runtime_api_smoke_test.time.monotonic",
                side_effect=[0.0, 0.1],
            ),
            patch("runtime_api_smoke_test.time.sleep"),
        ):
            rc = run_smoke_test(
                base_url="http://127.0.0.1:8000",
                prompt="hello",
                model="test-model",
                provider_url="http://localhost:11434",
                project_root=".",
                command_profile="python-playground",
                test_command="python test.py",
                expected_shells=("bash", "sh"),
                poll_interval_sec=0.01,
                timeout_sec=1.0,
            )

        self.assertEqual(rc, 0)
        self.assertEqual(request_json.call_count, 5)
        submit_payload = request_json.call_args_list[1].args[2]
        self.assertEqual(
            submit_payload["run"]["command_profile"],
            "python-playground",
        )
        self.assertEqual(
            submit_payload["run"]["test_command"],
            "python test.py",
        )

    def test_run_smoke_test_returns_one_on_failed_terminal_state(self) -> None:
        responses = [
            {"status": "ok"},
            {"job_id": "job-1"},
            {"status": "failed"},
            {"agent_stdout": "", "agent_stderr": "boom"},
        ]

        with (
            patch(
                "runtime_api_smoke_test._request_json",
                side_effect=responses,
            ),
            patch("runtime_api_smoke_test.time.monotonic", return_value=0.0),
            patch("runtime_api_smoke_test.time.sleep"),
        ):
            rc = run_smoke_test(
                base_url="http://127.0.0.1:8000",
                prompt="hello",
                model="test-model",
                provider_url="http://localhost:11434",
                project_root=".",
                command_profile="python-playground",
                test_command="python test.py",
                expected_shells=("bash", "sh"),
                poll_interval_sec=0.01,
                timeout_sec=1.0,
            )

        self.assertEqual(rc, 1)

    def test_run_smoke_test_returns_one_when_shell_missing(self) -> None:
        responses = [
            {"status": "ok"},
            {"job_id": "job-1"},
            {
                "status": "succeeded",
                "result": {
                    "test": {"returncode": 0},
                    "runtime_telemetry": {},
                },
            },
            {"agent_stdout": "done"},
        ]

        with (
            patch(
                "runtime_api_smoke_test._request_json",
                side_effect=responses,
            ),
            patch("runtime_api_smoke_test.time.monotonic", return_value=0.0),
            patch("runtime_api_smoke_test.time.sleep"),
        ):
            rc = run_smoke_test(
                base_url="http://127.0.0.1:8000",
                prompt="hello",
                model="test-model",
                provider_url="http://localhost:11434",
                project_root=".",
                command_profile="python-playground",
                test_command="python test.py",
                expected_shells=("bash", "sh"),
                poll_interval_sec=0.01,
                timeout_sec=1.0,
            )

        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
