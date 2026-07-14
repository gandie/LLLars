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
