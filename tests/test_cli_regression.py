from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lllars_core.cli import main
from lllars_core.runtime_models import RunResult


class CliRegressionTests(unittest.TestCase):
    def test_oneshot_requires_prompt_or_prompt_file(self) -> None:
        cfg = SimpleNamespace(
            model="test-model",
            provider_url="http://localhost:11434",
            project_root=Path("playground").resolve(),
            mount_work_root=Path("playground").resolve(),
            command_profile="none",
            test_command=None,
            eval_command=None,
        )

        with (
            patch.object(
                sys,
                "argv",
                ["lllars", "--config", "playground.example.json"],
            ),
            patch("lllars_core.cli.load_config", return_value=cfg),
        ):
            with self.assertRaisesRegex(
                SystemExit,
                "Provide --prompt or --prompt-file",
            ):
                main()

    def test_oneshot_uses_run_job_and_returns_success_exit_code(self) -> None:
        cfg = SimpleNamespace(
            model="test-model",
            provider_url="http://localhost:11434",
            project_root=Path("playground").resolve(),
            mount_work_root=Path("playground").resolve(),
            command_profile="none",
            test_command=None,
            eval_command=None,
        )

        with (
            patch.object(
                sys,
                "argv",
                [
                    "lllars",
                    "--config",
                    "playground.example.json",
                    "--prompt",
                    "hello",
                    "--timeout-sec",
                    "7",
                ],
            ),
            patch("lllars_core.cli.load_config", return_value=cfg),
            patch("lllars_core.cli._print_runtime_startup"),
            patch("lllars_core.cli._run_startup_preflight"),
            patch(
                "lllars_core.cli.run_job",
                return_value=RunResult(
                    success=True,
                    agent_returncode=0,
                    elapsed_sec=0.01,
                    agent_stdout="ok",
                    agent_stderr="",
                ),
            ) as run_job,
            patch("lllars_core.cli.print_summary") as print_summary,
        ):
            with self.assertRaises(SystemExit) as exit_ctx:
                main()

        self.assertEqual(exit_ctx.exception.code, 0)
        self.assertEqual(run_job.call_count, 1)

        call = run_job.call_args
        self.assertEqual(call.kwargs["cfg"], cfg)
        self.assertTrue(call.kwargs["show_progress"])
        self.assertTrue(call.kwargs["emit_status"])

        spec = call.args[0]
        self.assertEqual(spec.prompt, "hello")
        self.assertEqual(spec.timeout_sec, 7)
        self.assertEqual(
            spec.config_path,
            str(Path("playground.example.json").resolve()),
        )
        print_summary.assert_called_once()

    def test_serve_uses_runtime_app_with_uvicorn(self) -> None:
        cfg = SimpleNamespace(
            queue_backend="inmemory",
            service_host="127.0.0.1",
            service_port=8123,
            service_workers=1,
        )

        with (
            patch.object(
                sys,
                "argv",
                [
                    "lllars",
                    "serve",
                    "--config",
                    "playground.example.json",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8123",
                    "--workers",
                    "2",
                    "--queue-backend",
                    "inmemory",
                ],
            ),
            patch("lllars_core.cli.load_config", return_value=cfg),
            patch("lllars_core.cli._print_runtime_startup"),
            patch("lllars_core.cli._run_startup_preflight"),
            patch(
                "lllars_core.cli.create_runtime_app",
                return_value="app",
            ) as create_app,
            patch("uvicorn.run") as uvicorn_run,
        ):
            main()

        create_app.assert_called_once_with(cfg)
        uvicorn_run.assert_called_once_with(
            "app",
            host="127.0.0.1",
            port=8123,
            log_level="info",
        )

    def test_serve_rejects_unsupported_queue_backend(self) -> None:
        cfg = SimpleNamespace(
            queue_backend="redis",
            service_host="127.0.0.1",
            service_port=8000,
            service_workers=1,
        )

        with (
            patch.object(
                sys,
                "argv",
                [
                    "lllars",
                    "serve",
                    "--config",
                    "playground.example.json",
                    "--queue-backend",
                    "redis",
                ],
            ),
            patch("lllars_core.cli.load_config", return_value=cfg),
            patch("lllars_core.cli._print_runtime_startup"),
            patch("lllars_core.cli._run_startup_preflight"),
        ):
            with self.assertRaisesRegex(
                SystemExit,
                "Serve mode currently supports only queue_backend=inmemory",
            ):
                main()


if __name__ == "__main__":
    unittest.main()
