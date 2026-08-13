from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lllars_core.config import load_config
from lllars_core.runtime.job_runner import run_job

from runtime_runner_test_support import basic_spec, powershell_selection


def _setup_override_fixture(root: Path) -> tuple[Path, Path, object]:
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
    return proj_b, config_path, load_config(config_path)


def _setup_external_profile_fixture(root: Path) -> tuple[Path, object]:
    workspace = root / "workspace"
    (workspace / "proj").mkdir(parents=True)
    (root / "profiles.yaml").write_text(
        "profiles:\n"
        "  default-shell:\n"
        "    - python /tmp/default.py\n"
        "  lint-only:\n"
        "    - python -m pytest -q\n",
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
            "project_root": "workspace/proj",
            "commands": {},
            "command_profile": "default-shell",
            "command_profiles_path": "profiles.yaml",
        },
    }
    config_path = root / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path, load_config(config_path)


def _setup_wildcard_profile_fixture(root: Path) -> tuple[Path, object]:
    workspace = root / "workspace"
    (workspace / "proj").mkdir(parents=True)
    (root / "profiles.yaml").write_text(
        "profiles:\n"
        "  wildcard:\n"
        "    - python *.py\n",
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
            "project_root": "workspace/proj",
            "commands": {},
            "command_profile": "wildcard",
            "command_profiles_path": "profiles.yaml",
        },
    }
    config_path = root / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path, load_config(config_path)


def _run_job_with_patched_agent(spec, cfg):
    with (
        patch(
            "lllars_core.runtime.job_runner.detect_shell",
            return_value=powershell_selection(),
        ),
        patch(
            "lllars_core.runtime.job_runner.run_agent_with_timeout",
            return_value=("", "", 0, {}, []),
        ) as run_agent,
        patch(
            "lllars_core.runtime.job_runner.is_eval_success",
            return_value=True,
        ),
    ):
        run_job(spec, cfg=cfg)
    return run_agent.call_args.kwargs["cfg"]


class RuntimeRunnerOverrideTests(unittest.TestCase):
    def test_run_job_allows_job_level_skills_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            proj_b, _, cfg = _setup_override_fixture(root)

            with (
                patch(
                    "lllars_core.runtime.job_runner.detect_shell",
                    return_value=powershell_selection(),
                ),
                patch(
                    "lllars_core.runtime.job_runner.run_agent_with_timeout",
                    return_value=("", "", 0, {}, []),
                ) as run_agent,
                patch(
                    "lllars_core.runtime.job_runner.is_eval_success",
                    return_value=True,
                ),
            ):
                run_job(
                    basic_spec(
                        run_overrides={
                            "project_root": "proj-b",
                            "commands": {},
                            "skills_enabled": False,
                        }
                    ),
                    cfg=cfg,
                )

            effective_cfg = run_agent.call_args.kwargs["cfg"]
            self.assertEqual(effective_cfg.project_root, proj_b.resolve())
            self.assertFalse(effective_cfg.skills_enabled)

    def test_run_job_overrides_to_external_profile_from_loaded_map(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path, cfg = _setup_external_profile_fixture(root)
            spec = basic_spec(
                config_path=str(config_path),
                run_overrides={
                    "project_root": "proj",
                    "commands": {},
                    "command_profile": "lint-only",
                },
            )
            effective_cfg = _run_job_with_patched_agent(spec, cfg)
            self.assertEqual(effective_cfg.command_profile, "lint-only")
            self.assertEqual(
                effective_cfg.allowed_shell_commands,
                ("python -m pytest -q",),
            )

    def test_run_job_preserves_wildcard_profile_command_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path, cfg = _setup_wildcard_profile_fixture(root)
            spec = basic_spec(
                config_path=str(config_path),
                run_overrides={
                    "project_root": "proj",
                    "commands": {},
                    "command_profile": "wildcard",
                },
            )
            effective_cfg = _run_job_with_patched_agent(spec, cfg)
            self.assertEqual(effective_cfg.command_profile, "wildcard")
            self.assertEqual(
                effective_cfg.allowed_shell_commands,
                ("python *",),
            )


if __name__ == "__main__":
    unittest.main()
