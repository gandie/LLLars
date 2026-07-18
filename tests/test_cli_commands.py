from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from cli_test_support import base_run_cfg
from lllars_core.cli import main
from lllars_core.runtime.models import RunResult


def _oneshot_argv() -> list[str]:
    return [
        "lllars",
        "--config",
        "playground.example.json",
        "--prompt",
        "hello",
        "--timeout-sec",
        "7",
    ]


def _serve_cfg(*, queue_backend: str, port: int) -> object:
    return type(
        "Cfg",
        (),
        {
            "queue_backend": queue_backend,
            "service_host": "127.0.0.1",
            "service_port": port,
            "service_workers": 1,
        },
    )


def _serve_argv(queue_backend: str) -> list[str]:
    return [
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
        queue_backend,
    ]


class CliCommandTests(unittest.TestCase):
    def test_oneshot_requires_prompt_or_prompt_file(self) -> None:
        cfg = base_run_cfg()
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
        cfg = base_run_cfg()
        with (
            patch.object(sys, "argv", _oneshot_argv()),
            patch("lllars_core.cli.load_config", return_value=cfg),
            patch("lllars_core.cli.print_runtime_startup"),
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
        call = run_job.call_args
        self.assertEqual(call.kwargs["cfg"], cfg)
        self.assertTrue(call.kwargs["show_progress"])
        self.assertTrue(call.kwargs["emit_status"])
        self.assertEqual(call.args[0].prompt, "hello")
        self.assertEqual(call.args[0].timeout_sec, 7)
        self.assertEqual(
            call.args[0].config_path,
            str(Path("playground.example.json").resolve()),
        )
        print_summary.assert_called_once()

    def test_serve_uses_runtime_app_with_uvicorn(self) -> None:
        cfg = _serve_cfg(queue_backend="inmemory", port=8123)
        with (
            patch.object(sys, "argv", _serve_argv("inmemory")),
            patch("lllars_core.cli.load_config", return_value=cfg),
            patch("lllars_core.cli.print_runtime_startup"),
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
        cfg = _serve_cfg(queue_backend="redis", port=8000)
        with (
            patch.object(sys, "argv", _serve_argv("redis")),
            patch("lllars_core.cli.load_config", return_value=cfg),
            patch("lllars_core.cli.print_runtime_startup"),
            patch("lllars_core.cli._run_startup_preflight"),
        ):
            with self.assertRaisesRegex(
                SystemExit,
                "Serve mode currently supports only queue_backend=inmemory",
            ):
                main()


if __name__ == "__main__":
    unittest.main()
