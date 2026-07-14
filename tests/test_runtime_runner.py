from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lllars_core.runtime_models import JobSpec
from lllars_core.runtime_runner import run_job


class RuntimeRunnerTests(unittest.TestCase):
    def test_run_job_returns_runresult_with_telemetry_passthrough(
        self,
    ) -> None:
        cfg = SimpleNamespace(test_command="pytest", eval_command="eval")
        status_messages: list[str] = []

        with (
            patch(
                "lllars_core.runtime_runner.run_agent_with_timeout",
                return_value=(
                    "agent-out",
                    "",
                    0,
                    {"requests": 2, "tool_calls": 1},
                    ["trace-1"],
                ),
            ) as run_agent,
            patch(
                "lllars_core.runtime_runner.run_tests",
                return_value={"returncode": 0, "stdout": "ok", "stderr": ""},
            ),
            patch(
                "lllars_core.runtime_runner.run_eval",
                return_value=({"summary": {"pass_rate": 100.0}}, None),
            ),
            patch(
                "lllars_core.runtime_runner.is_eval_success",
                return_value=True,
            ),
        ):
            result = run_job(
                JobSpec(prompt="hello", timeout_sec=42),
                cfg=cfg,
                show_progress=True,
                emit_status=status_messages.append,
            )

        run_agent.assert_called_once_with(
            cfg=cfg,
            prompt_text="hello",
            timeout_sec=42,
            show_progress=True,
        )
        self.assertEqual(status_messages, ["running tests", "running eval"])
        self.assertTrue(result.success)
        self.assertEqual(result.agent_returncode, 0)
        self.assertEqual(result.agent_stdout, "agent-out")
        self.assertEqual(
            result.runtime_telemetry,
            {"requests": 2, "tool_calls": 1},
        )
        self.assertEqual(result.thought_trace, ["trace-1"])

    def test_run_job_loads_config_from_spec_path_when_cfg_missing(
        self,
    ) -> None:
        cfg = SimpleNamespace(test_command=None, eval_command=None)

        with (
            patch(
                "lllars_core.runtime_runner.load_config",
                return_value=cfg,
            ) as load_cfg,
            patch(
                "lllars_core.runtime_runner.run_agent_with_timeout",
                return_value=("", "", 0, {}, []),
            ),
            patch(
                "lllars_core.runtime_runner.run_tests",
                return_value={
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                    "skipped": True,
                },
            ),
            patch(
                "lllars_core.runtime_runner.run_eval",
                return_value=(None, None),
            ),
            patch(
                "lllars_core.runtime_runner.is_eval_success",
                return_value=True,
            ),
        ):
            run_job(
                JobSpec(
                    prompt="hello",
                    config_path="playground.example.json",
                    timeout_sec=5,
                )
            )

        load_cfg.assert_called_once()
        resolved_path = load_cfg.call_args.args[0]
        self.assertEqual(
            resolved_path,
            Path("playground.example.json").resolve(),
        )


if __name__ == "__main__":
    unittest.main()
