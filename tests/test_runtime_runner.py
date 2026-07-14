from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lllars_core.config import load_config
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
                JobSpec(
                    prompt="hello",
                    run={
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": ".",
                        "command_profile": "none",
                    },
                    timeout_sec=42,
                ),
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
                    run={
                        "model": "test-model",
                        "provider_url": "http://localhost:11434",
                        "project_root": ".",
                        "command_profile": "none",
                    },
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

    def test_run_job_allows_job_level_skills_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            proj_a = workspace / "proj-a"
            proj_b = workspace / "proj-b"
            (proj_a / "skills").mkdir(parents=True)
            proj_b.mkdir(parents=True)

            (proj_a / "skills" / "demo.md").write_text(
                "---\nid: demo\ndescription: demo\n---\ncontent",
                encoding="utf-8",
            )

            config = {
                "service": {
                    "mode": "serve",
                    "mount_work_root": "workspace",
                    "mount_config_root": ".",
                    "mount_artifacts_root": ".",
                    "queue_backend": "inmemory",
                    "network_policy": "inherit",
                },
                "run": {
                    "model": "test-model",
                    "provider_url": "http://localhost:11434",
                    "project_root": "workspace/proj-a",
                    "commands": {},
                    "command_profile": "none",
                    "skills_enabled": True,
                    "skills_glob": "skills/*.md",
                },
            }

            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            cfg = load_config(config_path)

            with (
                patch(
                    "lllars_core.runtime_runner.run_agent_with_timeout",
                    return_value=("", "", 0, {}, []),
                ) as run_agent,
                patch(
                    "lllars_core.runtime_runner.run_tests",
                    return_value={"returncode": 0, "stdout": "", "stderr": ""},
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
                        run={
                            "model": "test-model",
                            "provider_url": "http://localhost:11434",
                            "project_root": "proj-b",
                            "commands": {},
                            "command_profile": "none",
                            "skills_enabled": False,
                        },
                        timeout_sec=5,
                    ),
                    cfg=cfg,
                )

            effective_cfg = run_agent.call_args.kwargs["cfg"]
            self.assertEqual(effective_cfg.project_root, proj_b.resolve())
            self.assertFalse(effective_cfg.skills_enabled)


if __name__ == "__main__":
    unittest.main()
