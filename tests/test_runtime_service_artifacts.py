from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lllars_core.runtime.models import JobSpec, RunResult
from lllars_core.runtime.service import RuntimeService


def _spec() -> JobSpec:
    return JobSpec(
        prompt="hello",
        run={
            "model": "test-model",
            "provider_url": "http://localhost:11434",
            "project_root": ".",
            "command_profile": "none",
        },
        timeout_sec=5,
    )


class RuntimeServiceArtifactsTests(unittest.TestCase):
    def test_runtime_service_persists_artifacts_on_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = SimpleNamespace(mount_artifacts_root=Path(tmpdir))
            service = RuntimeService(cfg=cfg)
            spec = service.store.create(_spec(), job_id="job-success").spec

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
            summary_path = Path(tmpdir) / record.artifacts["summary"]
            stdout_path = Path(tmpdir) / record.artifacts["stdout"]
            telemetry_path = Path(tmpdir) / record.artifacts["telemetry"]
            self.assertTrue(summary_path.exists())
            self.assertTrue(stdout_path.exists())
            self.assertTrue(telemetry_path.exists())
            self.assertEqual(stdout_path.read_text(encoding="utf-8"), "agent-out")
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["job_id"], "job-success")
            self.assertEqual(summary["status"], "succeeded")

    def test_runtime_service_persists_artifacts_on_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = SimpleNamespace(mount_artifacts_root=Path(tmpdir))
            service = RuntimeService(cfg=cfg)
            spec = service.store.create(_spec(), job_id="job-failure").spec

            with patch("lllars_core.runtime.service.run_job", side_effect=RuntimeError("boom")):
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


if __name__ == "__main__":
    unittest.main()
