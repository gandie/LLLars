from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config_test_support import base_config, write_config
from lllars_core.config import load_config


class ConfigRuntimePathTests(unittest.TestCase):
    def test_unknown_command_profile_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            payload = base_config(
                project_root="workspace/project", mount_work_root="workspace"
            )
            payload["run"]["command_profile"] = "does-not-exist"
            with self.assertRaisesRegex(ValueError, "Unknown command_profile"):
                load_config(write_config(root, payload))

    def test_known_command_profile_exposes_expected_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            payload = base_config(
                project_root="workspace/project", mount_work_root="workspace"
            )
            payload["run"]["command_profile"] = "python-playground"
            cfg = load_config(write_config(root, payload))
            self.assertEqual(cfg.command_profile, "python-playground")
            self.assertEqual(
                cfg.allowed_shell_commands,
                ("python main.py", "python test.py"),
            )

    def test_project_root_must_resolve_under_mount_work_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            cfg = load_config(
                write_config(
                    root,
                    base_config(
                        "workspace/project", mount_work_root="workspace"
                    ),
                )
            )
            self.assertEqual(
                cfg.project_root, (root / "workspace" / "project").resolve()
            )
            self.assertEqual(
                cfg.mount_work_root, (root / "workspace").resolve()
            )

    def test_project_root_parent_traversal_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace").mkdir(parents=True)
            (root / "outside").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "parent traversal"):
                load_config(
                    write_config(
                        root,
                        base_config("../outside", mount_work_root="workspace"),
                    )
                )

    def test_project_root_absolute_path_is_denied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            absolute_project = str((root / "workspace" / "project").resolve())
            with self.assertRaisesRegex(ValueError, "absolute paths"):
                load_config(
                    write_config(
                        root,
                        base_config(
                            absolute_project, mount_work_root="workspace"
                        ),
                    )
                )

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
            with self.assertRaisesRegex(ValueError, "escapes mount_work_root"):
                load_config(
                    write_config(
                        root,
                        base_config(
                            "workspace/project-link",
                            mount_work_root="workspace",
                        ),
                    )
                )

    def test_shell_mode_defaults_to_auto(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            cfg = load_config(
                write_config(
                    root,
                    base_config(
                        "workspace/project", mount_work_root="workspace"
                    ),
                )
            )
            self.assertEqual(cfg.shell_mode, "auto")
            self.assertIsNone(cfg.shell_override)

    def test_unknown_shell_override_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            payload = base_config(
                "workspace/project", mount_work_root="workspace"
            )
            payload["run"]["shell_override"] = "fish"
            with self.assertRaisesRegex(ValueError, "Unknown shell_override"):
                load_config(write_config(root, payload))

    def test_override_mode_requires_shell_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            payload = base_config(
                "workspace/project", mount_work_root="workspace"
            )
            payload["run"]["shell_mode"] = "override"
            with self.assertRaisesRegex(
                ValueError,
                "shell_mode=override requires non-empty shell_override",
            ):
                load_config(write_config(root, payload))

    def test_shell_override_is_platform_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            payload = base_config(
                "workspace/project", mount_work_root="workspace"
            )
            payload["run"]["shell_override"] = "cmd"
            with patch(
                "lllars_core.config.platform.system", return_value="Linux"
            ):
                with self.assertRaisesRegex(
                    ValueError, "Unsupported shell_override"
                ):
                    load_config(write_config(root, payload))


if __name__ == "__main__":
    unittest.main()
