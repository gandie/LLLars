from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from lllars_core.runtime.job_runner import run_job

from runtime_runner_test_support import basic_spec, powershell_selection


def _timeout_outcome() -> tuple[str, str, int, dict[str, int], list[str]]:
    return "", "[lllars] agent timed out", 124, {"requests": 1}, []


class RuntimeRunnerDeadlineTests(unittest.TestCase):
    def _run_deadline_case(self, *, deadline_at: datetime):
        cfg = SimpleNamespace(test_command="pytest", eval_command="eval")
        with (
            patch(
                "lllars_core.runtime.job_runner.run_agent_with_timeout",
                return_value=_timeout_outcome(),
            ) as run_agent,
            patch(
                "lllars_core.runtime.job_runner.detect_shell",
                return_value=powershell_selection(),
            ),
            patch("lllars_core.runtime.job_runner.run_shell") as run_shell,
            patch("lllars_core.runtime.job_runner.is_eval_success") as is_eval,
        ):
            result = run_job(
                basic_spec(timeout_sec=42, deadline_at=deadline_at),
                cfg=cfg,
            )
        return run_agent, run_shell, is_eval, result

    def test_deadline_expired_before_start_short_circuits_agent(self) -> None:
        run_agent, run_shell, is_eval, result = self._run_deadline_case(
            deadline_at=datetime.now() - timedelta(seconds=1)
        )

        run_agent.assert_not_called()
        run_shell.assert_not_called()
        is_eval.assert_not_called()
        self.assertEqual(result.agent_returncode, 124)
        self.assertEqual(result.eval_error, "timeout")
        deadline = result.runtime_telemetry["deadline"]
        self.assertTrue(deadline["expired_before_start"])
        self.assertTrue(deadline["reached"])

    def test_deadline_limits_timeout_and_marks_reached(self) -> None:
        run_agent, run_shell, is_eval, result = self._run_deadline_case(
            deadline_at=datetime.now() + timedelta(seconds=3)
        )

        run_agent.assert_called_once()
        run_shell.assert_not_called()
        is_eval.assert_not_called()
        timeout_arg = run_agent.call_args.kwargs["timeout_sec"]
        self.assertLess(timeout_arg, 42)
        self.assertEqual(result.agent_returncode, 124)
        self.assertEqual(result.eval_error, "timeout")
        deadline = result.runtime_telemetry["deadline"]
        self.assertTrue(deadline["deadline_limited"])
        self.assertTrue(deadline["reached"])


if __name__ == "__main__":
    unittest.main()
