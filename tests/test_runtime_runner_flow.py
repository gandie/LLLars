from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lllars_core.runtime.job_runner import run_job

from runtime_runner_test_support import basic_spec, powershell_selection, resolved_config_path


def _expected_telemetry() -> dict[str, object]:
    return {
        "requests": 2,
        "tool_calls": 1,
        "shell": {
            "selected": "powershell",
            "shell_mode": "auto",
            "shell_override": None,
            "invocation_mode": "auto_detect",
        },
    }


def _run_success_case() -> tuple[object, object, list[str]]:
    cfg = SimpleNamespace(test_command="pytest", eval_command="eval")
    status_messages: list[str] = []
    with (
        patch(
            "lllars_core.runtime.job_runner.run_agent_with_timeout",
            return_value=("agent-out", "", 0, {"requests": 2, "tool_calls": 1}, ["trace-1"]),
        ) as run_agent,
        patch("lllars_core.runtime.job_runner.detect_shell", return_value=powershell_selection()),
        patch(
            "lllars_core.runtime.job_runner.run_shell",
            side_effect=[
                {"returncode": 0, "stdout": "ok", "stderr": "", "shell": "powershell"},
                {"returncode": 0, "stdout": '{"summary":{"pass_rate":100.0}}', "stderr": "", "shell": "powershell"},
            ],
        ),
        patch("lllars_core.runtime.job_runner.is_eval_success", return_value=True),
    ):
        result = run_job(basic_spec(timeout_sec=42), cfg=cfg, show_progress=True, emit_status=status_messages.append)
    return run_agent, result, status_messages


class RuntimeRunnerFlowTests(unittest.TestCase):
    def test_run_job_returns_runresult_with_telemetry_passthrough(self) -> None:
        run_agent, result, status_messages = _run_success_case()
        cfg = run_agent.call_args.kwargs["cfg"]
        run_agent.assert_called_once_with(cfg=cfg, prompt_text="hello", timeout_sec=42, show_progress=True, cancel_requested=None)
        self.assertEqual(status_messages, ["running tests", "running eval"])
        self.assertTrue(result.success)
        self.assertEqual(result.agent_returncode, 0)
        self.assertEqual(result.agent_stdout, "agent-out")
        self.assertEqual(result.thought_trace, ["trace-1"])
        self.assertEqual(result.runtime_telemetry, _expected_telemetry())

    def test_run_job_loads_config_from_spec_path_when_cfg_missing(self) -> None:
        cfg = SimpleNamespace(test_command=None, eval_command=None)
        with (
            patch("lllars_core.runtime.job_runner.load_config", return_value=cfg) as load_cfg,
            patch("lllars_core.runtime.job_runner.detect_shell", return_value=powershell_selection()),
            patch("lllars_core.runtime.job_runner.run_agent_with_timeout", return_value=("", "", 0, {}, [])),
            patch("lllars_core.runtime.job_runner.is_eval_success", return_value=True),
        ):
            run_job(basic_spec(config_path="playground.example.json"))
        load_cfg.assert_called_once()
        resolved_path = load_cfg.call_args.args[0]
        self.assertEqual(resolved_path, resolved_config_path())

    def test_run_job_returns_canceled_before_tests_and_eval(self) -> None:
        cfg = SimpleNamespace(test_command="pytest", eval_command="eval")
        with (
            patch(
                "lllars_core.runtime.job_runner.run_agent_with_timeout",
                return_value=("", "[lllars] agent canceled", 130, {"requests": 1}, []),
            ) as run_agent,
            patch("lllars_core.runtime.job_runner.detect_shell", return_value=powershell_selection()),
            patch("lllars_core.runtime.job_runner.run_shell") as run_shell,
            patch("lllars_core.runtime.job_runner.is_eval_success") as is_eval,
        ):
            result = run_job(basic_spec(timeout_sec=42), cfg=cfg, cancel_requested=lambda: True)
        run_agent.assert_called_once()
        run_shell.assert_not_called()
        is_eval.assert_not_called()
        self.assertFalse(result.success)
        self.assertEqual(result.agent_returncode, 130)
        self.assertEqual(result.eval_error, "canceled")
        self.assertEqual(result.test, {})


if __name__ == "__main__":
    unittest.main()
