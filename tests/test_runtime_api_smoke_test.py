from __future__ import annotations

import unittest

from runtime_api_smoke_test import run_smoke_test
from runtime_api_smoke_harness import serve_harness


class RuntimeApiSmokeScriptTests(unittest.TestCase):
    def test_run_smoke_test_returns_zero_on_succeeded_terminal_state(
        self,
    ) -> None:
        with serve_harness(
            [
                {"status": "running"},
                {
                    "status": "succeeded",
                    "result": {
                        "test": {"returncode": 0},
                        "runtime_telemetry": {"shell": {"selected": "bash"}},
                    },
                },
            ]
        ) as harness:
            rc = run_smoke_test(
                base_url=harness.base_url,
                prompt="hello",
                model="test-model",
                provider_url="http://localhost:11434",
                project_root=".",
                command_profile="python-playground",
                test_command="python test.py",
                expected_shells=("bash", "sh"),
                poll_interval_sec=0.001,
                timeout_sec=1.0,
            )

        self.assertEqual(rc, 0)
        self.assertEqual(len(harness.submissions), 1)
        run_payload = harness.submissions[0]["run"]
        self.assertEqual(run_payload["command_profile"], "python-playground")
        self.assertEqual(run_payload["test_command"], "python test.py")

    def test_run_smoke_test_returns_one_on_failed_terminal_state(self) -> None:
        with serve_harness([{"status": "failed"}]) as harness:
            rc = run_smoke_test(
                base_url=harness.base_url,
                prompt="hello",
                model="test-model",
                provider_url="http://localhost:11434",
                project_root=".",
                command_profile="python-playground",
                test_command="python test.py",
                expected_shells=("bash", "sh"),
                poll_interval_sec=0.001,
                timeout_sec=1.0,
            )

        self.assertEqual(rc, 1)

    def test_run_smoke_test_returns_one_on_canceled_terminal_state(
        self,
    ) -> None:
        with serve_harness([{"status": "canceled"}]) as harness:
            rc = run_smoke_test(
                base_url=harness.base_url,
                prompt="hello",
                model="test-model",
                provider_url="http://localhost:11434",
                project_root=".",
                command_profile="python-playground",
                test_command="python test.py",
                expected_shells=("bash", "sh"),
                poll_interval_sec=0.001,
                timeout_sec=1.0,
            )

        self.assertEqual(rc, 1)

    def test_run_smoke_test_timeout_is_deterministic(self) -> None:
        with serve_harness([{"status": "running"}]) as harness:
            with self.assertRaisesRegex(
                TimeoutError,
                "Timed out waiting for terminal",
            ):
                run_smoke_test(
                    base_url=harness.base_url,
                    prompt="hello",
                    model="test-model",
                    provider_url="http://localhost:11434",
                    project_root=".",
                    command_profile="python-playground",
                    test_command="python test.py",
                    expected_shells=("bash", "sh"),
                    poll_interval_sec=0.01,
                    timeout_sec=0.1,
                    monotonic=iter([0.0, 0.2]).__next__,
                    sleep=lambda _: None,
                )

    def test_run_smoke_test_returns_one_when_shell_missing(self) -> None:
        with serve_harness(
            [
                {
                    "status": "succeeded",
                    "result": {
                        "test": {"returncode": 0},
                        "runtime_telemetry": {},
                    },
                }
            ]
        ) as harness:
            rc = run_smoke_test(
                base_url=harness.base_url,
                prompt="hello",
                model="test-model",
                provider_url="http://localhost:11434",
                project_root=".",
                command_profile="python-playground",
                test_command="python test.py",
                expected_shells=("bash", "sh"),
                poll_interval_sec=0.001,
                timeout_sec=1.0,
            )

        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
