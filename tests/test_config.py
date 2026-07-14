from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from lllars_core.config import load_config


def _base_config(
    project_root: str,
    *,
    mount_work_root: str | None,
) -> dict[str, object]:
    config: dict[str, object] = {
        "model": "test-model",
        "provider-url": "http://localhost:11434",
        "project_root": project_root,
        "commands": {},
        "command_profile": "none",
    }
    if mount_work_root is not None:
        config["mount_work_root"] = mount_work_root
    return config


class ConfigFilesystemBoundaryTests(unittest.TestCase):
    def test_split_service_only_config_is_supported_without_run_settings(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace").mkdir(parents=True)

            config = {
                "service": {
                    "mode": "serve",
                    "host": "0.0.0.0",
                    "port": 9000,
                    "workers": 1,
                    "mount_work_root": "workspace",
                    "mount_config_root": ".",
                    "mount_artifacts_root": ".",
                    "queue_backend": "inmemory",
                    "network_policy": "inherit",
                },
            }

            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            cfg = load_config(config_path)

            self.assertEqual(cfg.service_mode, "serve")
            self.assertEqual(cfg.model, "")
            self.assertEqual(cfg.provider_url, "")
            self.assertEqual(cfg.project_root, (root / "workspace").resolve())

    def test_split_service_only_config_is_supported_with_env_file(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)

            env_file = root / "runtime.env"
            env_file.write_text(
                "\n".join(
                    [
                        "MODEL=test-model",
                        "OLLAMA_BASE_URL=http://localhost:11434",
                        "PROJECT_ROOT=workspace/project",
                        "COMMAND_PROFILE=none",
                    ]
                ),
                encoding="utf-8",
            )

            config = {
                "env_file": "runtime.env",
                "service": {
                    "mode": "serve",
                    "host": "0.0.0.0",
                    "port": 9000,
                    "workers": 1,
                    "mount_work_root": "workspace",
                    "mount_config_root": ".",
                    "mount_artifacts_root": ".",
                    "queue_backend": "inmemory",
                    "network_policy": "inherit",
                },
            }

            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            cfg = load_config(config_path)

            self.assertEqual(cfg.service_mode, "serve")
            self.assertEqual(cfg.run.model, "test-model")
            self.assertEqual(
                cfg.project_root,
                (root / "workspace" / "project").resolve(),
            )
            self.assertIsNone(cfg.test_command)
            self.assertIsNone(cfg.eval_command)

    def test_split_service_and_run_config_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)

            config = {
                "service": {
                    "mode": "serve",
                    "host": "0.0.0.0",
                    "port": 9000,
                    "workers": 2,
                    "mount_work_root": "workspace",
                    "mount_config_root": ".",
                    "mount_artifacts_root": ".",
                    "queue_backend": "inmemory",
                    "network_policy": "inherit",
                },
                "run": {
                    "model": "test-model",
                    "provider_url": "http://localhost:11434",
                    "project_root": "workspace/project",
                    "commands": {},
                    "command_profile": "python-playground",
                },
            }

            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            cfg = load_config(config_path)

            self.assertEqual(cfg.service_mode, "serve")
            self.assertEqual(cfg.service_host, "0.0.0.0")
            self.assertEqual(cfg.service_port, 9000)
            self.assertEqual(cfg.service_workers, 2)
            self.assertEqual(cfg.run.model, "test-model")
            self.assertEqual(cfg.run.command_profile, "python-playground")
            self.assertEqual(
                cfg.allowed_shell_commands,
                ("python main.py", "python test.py"),
            )

    def test_split_and_legacy_mix_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)

            config = {
                "service": {
                    "mount_work_root": "workspace",
                },
                "run": {
                    "model": "test-model",
                    "provider-url": "http://localhost:11434",
                    "project_root": "workspace/project",
                    "commands": {},
                    "command_profile": "none",
                },
                "queue_backend": "inmemory",
            }

            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "cannot mix split and legacy fields",
            ):
                load_config(config_path)

    def test_precedence_defaults_env_json_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)

            env_file = root / "runtime.env"
            env_file.write_text(
                "\n".join(
                    [
                        "SERVICE_PORT=9001",
                        "QUEUE_BACKEND=redis",
                        "TEST_COMMAND=python env-test.py",
                    ]
                ),
                encoding="utf-8",
            )

            config = {
                "env_file": "runtime.env",
                "service": {
                    "mount_work_root": "workspace",
                    "port": 9010,
                    "queue_backend": "inmemory",
                },
                "run": {
                    "model": "test-model",
                    "provider-url": "http://localhost:11434",
                    "project_root": "workspace/project",
                    "commands": {},
                    "command_profile": "none",
                },
            }

            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            cfg = load_config(
                config_path,
                overrides={
                    "service_port": 9020,
                    "queue_backend": "inmemory",
                },
            )

            self.assertEqual(cfg.service_port, 9020)
            self.assertEqual(cfg.queue_backend, "inmemory")
            self.assertIsNone(cfg.test_command)

    def test_unknown_command_profile_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)

            config = _base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            config["command_profile"] = "does-not-exist"

            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Unknown command_profile"):
                load_config(config_path)

    def test_known_command_profile_exposes_expected_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)

            config = _base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            config["command_profile"] = "python-playground"

            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            cfg = load_config(config_path)
            self.assertEqual(cfg.command_profile, "python-playground")
            self.assertEqual(
                cfg.allowed_shell_commands,
                ("python main.py", "python test.py"),
            )

    def test_project_root_must_resolve_under_mount_work_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)

            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    _base_config(
                        project_root="workspace/project",
                        mount_work_root="workspace",
                    )
                ),
                encoding="utf-8",
            )

            cfg = load_config(config_path)
            self.assertEqual(
                cfg.project_root,
                (root / "workspace" / "project").resolve(),
            )
            self.assertEqual(
                cfg.mount_work_root,
                (root / "workspace").resolve(),
            )

    def test_project_root_parent_traversal_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace").mkdir(parents=True)
            (root / "outside").mkdir(parents=True)

            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    _base_config(
                        project_root="../outside",
                        mount_work_root="workspace",
                    )
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "parent traversal"):
                load_config(config_path)

    def test_project_root_absolute_path_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)

            absolute_project = str((root / "workspace" / "project").resolve())
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    _base_config(
                        project_root=absolute_project,
                        mount_work_root="workspace",
                    )
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "absolute paths"):
                load_config(config_path)

    def test_project_root_symlink_escape_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir(parents=True)
            outside = root / "outside"
            outside.mkdir(parents=True)
            link = workspace / "project-link"

            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest(
                    "Symlink creation is not available in this environment"
                )

            if os.name == "nt" and not link.exists():
                self.skipTest("Windows symlink was not created")

            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    _base_config(
                        project_root="workspace/project-link",
                        mount_work_root="workspace",
                    )
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "escapes mount_work_root"):
                load_config(config_path)


if __name__ == "__main__":
    unittest.main()
