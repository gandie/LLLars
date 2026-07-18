from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from lllars_core.runtime import (
    RuntimeService as PackageRuntimeService,
    create_runtime_app as package_create_runtime_app,
)
from lllars_core.runtime.api import create_runtime_app
from lllars_core.runtime.job_runner import ShellAdapterUnavailableError
from lllars_core.runtime.models import JobSpec, RunResult
from lllars_core.runtime.service import RuntimeService


class RuntimeApiTests(unittest.TestCase):
    def test_runtime_package_exports_api_symbols(self) -> None:
        self.assertIs(package_create_runtime_app, create_runtime_app)
        self.assertIs(PackageRuntimeService, RuntimeService)

    def test_runtime_frontend_root_serves_html(self) -> None:
        cfg = SimpleNamespace(model="", provider_url="")
        app = create_runtime_app(cfg)
        client = TestClient(app)

        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("LLLars Runtime Console", response.text)
        self.assertIn("succeeded", response.text)
        self.assertIn("failed", response.text)
        self.assertIn("canceled", response.text)

    def test_submit_rejects_missing_run_fields_in_request(
        self,
    ) -> None:
        cfg = SimpleNamespace(model="", provider_url="")
        app = create_runtime_app(cfg)
        client = TestClient(app)

        submit_resp = client.post(
            "/jobs",
            json={"prompt": "hello", "timeout_sec": 5},
        )

        self.assertEqual(submit_resp.status_code, 422)

    def test_submit_accepts_extended_run_fields_in_request(self) -> None:
        cfg = SimpleNamespace(
            model="test-model",
            provider_url="http://localhost:11434",
        )
        app = create_runtime_app(cfg)
        client = TestClient(app)

        with patch(
            "lllars_core.runtime.service.run_job",
            return_value=RunResult(
                success=True,
                agent_returncode=0,
                elapsed_sec=0.01,
                agent_stdout="agent-out",
                agent_stderr="",
            ),
        ):
            submit_resp = client.post(
                "/jobs",
                json={
                    "prompt": "hello",
                    "run": {
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": "playground",
                        "commands": {},
                        "command_profile": "python-playground",
                        "eval_expect_json": False,
                        "eval_success_pass_rate": 100.0,
                        "usage_request_limit": None,
                        "usage_tool_calls_limit": 100,
                        "usage_input_tokens_limit": None,
                        "usage_output_tokens_limit": None,
                        "usage_total_tokens_limit": None,
                        "usage_count_tokens_before_request": False,
                        "agent_retries_tools": 1,
                        "agent_retries_output": 1,
                        "tool_timeout_sec": 90,
                        "max_concurrency": None,
                        "instrumentation_enabled": False,
                        "instrumentation_include_content": False,
                        "skills_enabled": True,
                        "skills_glob": "skills/*.md",
                        "skills_defer_loading": False,
                        "skills_require_description": True,
                        "mcp_enabled": False,
                        "mcp_config_path": None,
                        "mcp_init_timeout_sec": 60,
                        "system_prompt": "You are senior Python developer.",
                        "tool_policy": "Tool policy",
                    },
                    "timeout_sec": 5,
                },
            )

        self.assertEqual(submit_resp.status_code, 202)

    def test_submit_and_poll_until_terminal_state(self) -> None:
        cfg = SimpleNamespace(
            model="test-model",
            provider_url="http://localhost:11434",
        )
        app = create_runtime_app(cfg)
        client = TestClient(app)

        with patch(
            "lllars_core.runtime.service.run_job",
            return_value=RunResult(
                success=True,
                agent_returncode=0,
                elapsed_sec=0.01,
                agent_stdout="agent-out",
                agent_stderr="",
                thought_trace=["trace-1"],
            ),
        ):
            submit_resp = client.post(
                "/jobs",
                json={
                    "prompt": "hello",
                    "run": {
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": ".",
                        "command_profile": "none",
                    },
                    "timeout_sec": 5,
                },
            )

            self.assertEqual(submit_resp.status_code, 202)
            job_id = submit_resp.json()["job_id"]

            status_payload: dict[str, object] = {}
            for _ in range(60):
                status_resp = client.get(f"/jobs/{job_id}")
                self.assertEqual(status_resp.status_code, 200)
                status_payload = status_resp.json()
                if status_payload["status"] in {
                    "succeeded",
                    "failed",
                    "canceled",
                }:
                    break
                time.sleep(0.05)

            self.assertEqual(status_payload["status"], "succeeded")

            logs_resp = client.get(f"/jobs/{job_id}/logs")
            self.assertEqual(logs_resp.status_code, 200)
            logs_payload = logs_resp.json()
            self.assertEqual(logs_payload["agent_stdout"], "agent-out")
            self.assertEqual(logs_payload["thought_trace"], ["trace-1"])

    def test_cancel_force_terminates_inflight_job(self) -> None:
        cfg = SimpleNamespace(
            model="test-model",
            provider_url="http://localhost:11434",
        )
        app = create_runtime_app(cfg)
        client = TestClient(app)
        started = Event()

        def blocking_run_job(*args, **kwargs):
            _ = args
            cancel_requested = kwargs.get("cancel_requested")
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

        with patch(
            "lllars_core.runtime.service.run_job",
            side_effect=blocking_run_job,
        ):
            submit_resp = client.post(
                "/jobs",
                json={
                    "prompt": "hello",
                    "run": {
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": ".",
                        "command_profile": "none",
                    },
                    "timeout_sec": 5,
                },
            )

            self.assertEqual(submit_resp.status_code, 202)
            job_id = submit_resp.json()["job_id"]
            self.assertTrue(started.wait(timeout=1.0))

            cancel_resp = client.post(f"/jobs/{job_id}/cancel")
            self.assertEqual(cancel_resp.status_code, 200)
            self.assertEqual(cancel_resp.json()["status"], "canceled")

            status_payload: dict[str, object] = {}
            for _ in range(60):
                status_resp = client.get(f"/jobs/{job_id}")
                self.assertEqual(status_resp.status_code, 200)
                status_payload = status_resp.json()
                if status_payload["status"] in {
                    "succeeded",
                    "failed",
                    "canceled",
                }:
                    break
                time.sleep(0.05)

            self.assertEqual(status_payload["status"], "canceled")
            self.assertIsNone(status_payload["result"])
            self.assertEqual(status_payload["error"]["code"], "canceled")

    def test_unknown_job_returns_not_found(self) -> None:
        cfg = SimpleNamespace()
        app = create_runtime_app(cfg)
        client = TestClient(app)

        status_resp = client.get("/jobs/missing-job")
        self.assertEqual(status_resp.status_code, 404)

        cancel_resp = client.post("/jobs/missing-job/cancel")
        self.assertEqual(cancel_resp.status_code, 404)

        logs_resp = client.get("/jobs/missing-job/logs")
        self.assertEqual(logs_resp.status_code, 404)

    def test_submit_surfaces_shell_unavailable_envelope(self) -> None:
        cfg = SimpleNamespace(
            model="test-model",
            provider_url="http://localhost:11434",
        )
        app = create_runtime_app(cfg)
        client = TestClient(app)

        with patch(
            "lllars_core.runtime.service.run_job",
            side_effect=ShellAdapterUnavailableError(
                shell_mode="auto",
                shell_override=None,
            ),
        ):
            submit_resp = client.post(
                "/jobs",
                json={
                    "prompt": "hello",
                    "run": {
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": ".",
                        "command_profile": "none",
                    },
                    "timeout_sec": 5,
                },
            )

            self.assertEqual(submit_resp.status_code, 202)
            job_id = submit_resp.json()["job_id"]

            status_payload: dict[str, object] = {}
            for _ in range(60):
                status_resp = client.get(f"/jobs/{job_id}")
                self.assertEqual(status_resp.status_code, 200)
                status_payload = status_resp.json()
                if status_payload["status"] in {
                    "succeeded",
                    "failed",
                    "canceled",
                }:
                    break
                time.sleep(0.05)

            self.assertEqual(status_payload["status"], "failed")
            error_payload = status_payload["error"]
            self.assertEqual(error_payload["code"], "shell_unavailable")
            self.assertEqual(
                error_payload["details"],
                {"shell_mode": "auto", "shell_override": None},
            )

    def test_run_failed_error_includes_shell_metadata(self) -> None:
        cfg = SimpleNamespace(
            model="test-model",
            provider_url="http://localhost:11434",
        )
        app = create_runtime_app(cfg)
        client = TestClient(app)

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
            submit_resp = client.post(
                "/jobs",
                json={
                    "prompt": "hello",
                    "run": {
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": ".",
                        "command_profile": "none",
                    },
                    "timeout_sec": 5,
                },
            )

            self.assertEqual(submit_resp.status_code, 202)
            job_id = submit_resp.json()["job_id"]

            status_payload: dict[str, object] = {}
            for _ in range(60):
                status_resp = client.get(f"/jobs/{job_id}")
                self.assertEqual(status_resp.status_code, 200)
                status_payload = status_resp.json()
                if status_payload["status"] in {
                    "succeeded",
                    "failed",
                    "canceled",
                }:
                    break
                time.sleep(0.05)

            self.assertEqual(status_payload["status"], "failed")
            error_payload = status_payload["error"]
            self.assertEqual(error_payload["code"], "run_failed")
            self.assertEqual(error_payload["details"]["agent_returncode"], 1)
            self.assertEqual(
                error_payload["details"]["eval_error"],
                "eval failed",
            )
            self.assertIn("shell", error_payload["details"])

    def test_runtime_service_persists_artifacts_on_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = SimpleNamespace(mount_artifacts_root=Path(tmpdir))
            service = RuntimeService(cfg=cfg)
            spec = service.store.create(
                JobSpec(
                    prompt="hello",
                    run={
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": ".",
                        "command_profile": "none",
                    },
                    timeout_sec=5,
                ),
                job_id="job-success",
            ).spec

            with patch(
                "lllars_core.runtime.service.run_job",
                return_value=RunResult(
                    success=True,
                    agent_returncode=0,
                    elapsed_sec=0.01,
                    agent_stdout="agent-out",
                    agent_stderr="",
                    thought_trace=["trace-1"],
                    runtime_telemetry={"timeline": [{"event": "done"}]},
                ),
            ):
                service._run_job("job-success", spec)

            record = service.store.get("job-success")
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(record.status, "succeeded")

            summary_rel = record.artifacts["summary"]
            stdout_rel = record.artifacts["stdout"]
            telemetry_rel = record.artifacts["telemetry"]
            summary_path = Path(tmpdir) / summary_rel
            stdout_path = Path(tmpdir) / stdout_rel
            telemetry_path = Path(tmpdir) / telemetry_rel

            self.assertTrue(summary_path.exists())
            self.assertTrue(stdout_path.exists())
            self.assertTrue(telemetry_path.exists())
            self.assertEqual(
                stdout_path.read_text(encoding="utf-8"),
                "agent-out",
            )

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["job_id"], "job-success")
            self.assertEqual(summary["status"], "succeeded")

    def test_runtime_service_persists_artifacts_on_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = SimpleNamespace(mount_artifacts_root=Path(tmpdir))
            service = RuntimeService(cfg=cfg)
            spec = service.store.create(
                JobSpec(
                    prompt="hello",
                    run={
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": ".",
                        "command_profile": "none",
                    },
                    timeout_sec=5,
                ),
                job_id="job-failure",
            ).spec

            with patch(
                "lllars_core.runtime.service.run_job",
                side_effect=RuntimeError("boom"),
            ):
                service._run_job("job-failure", spec)

            record = service.store.get("job-failure")
            self.assertIsNotNone(record)
            assert record is not None
            self.assertEqual(record.status, "failed")
            self.assertIn("summary", record.artifacts)
            self.assertIn("stderr", record.artifacts)

            summary_path = Path(tmpdir) / record.artifacts["summary"]
            stderr_path = Path(tmpdir) / record.artifacts["stderr"]
            self.assertTrue(summary_path.exists())
            self.assertTrue(stderr_path.exists())

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "failed")
            self.assertEqual(summary["error"]["code"], "run_exception")

    def test_runtime_frontend_fallback_when_static_missing(self) -> None:
        cfg = SimpleNamespace(model="", provider_url="")

        with patch(
            "lllars_core.runtime.web.RUNTIME_UI_DIR",
            Path("missing-ui"),
        ):
            app = create_runtime_app(cfg)

        client = TestClient(app)
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "ui": "unavailable"},
        )


if __name__ == "__main__":
    unittest.main()
