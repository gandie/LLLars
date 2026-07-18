from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from lllars_core.runtime import run_job as package_run_job
from lllars_core.runtime import ShellAdapterUnavailableError as package_shell_error
from lllars_core.runtime.job_runner import ShellAdapterUnavailableError, run_job

from runtime_runner_test_support import basic_spec


class RuntimeRunnerExportTests(unittest.TestCase):
    def test_runtime_package_exports_runner_symbols(self) -> None:
        self.assertIs(package_run_job, run_job)
        self.assertIs(package_shell_error, ShellAdapterUnavailableError)

    def test_run_job_raises_when_no_supported_shell_is_available(self) -> None:
        cfg = SimpleNamespace(
            test_command="python -V",
            eval_command=None,
            project_root=".",
            eval_expect_json=False,
            shell_mode="auto",
            shell_override=None,
        )
        with (
            patch("lllars_core.runtime.job_runner.detect_shell", return_value=None),
            patch("lllars_core.runtime.job_runner.run_agent_with_timeout") as run_agent,
        ):
            with self.assertRaises(ShellAdapterUnavailableError):
                run_job(basic_spec(), cfg=cfg)
        run_agent.assert_not_called()


if __name__ == "__main__":
    unittest.main()
