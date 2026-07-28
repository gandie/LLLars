from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from config_test_support import base_config, write_config
from lllars_core.config import load_config


def _workspace_root(temp_dir: str) -> Path:
    root = Path(temp_dir)
    (root / "workspace" / "project").mkdir(parents=True)
    return root


class ConfigToolRegistrySettingsTests(unittest.TestCase):
    def test_default_enabled_tool_groups_match_native_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            cfg = load_config(write_config(root, payload))
            self.assertEqual(
                cfg.enabled_tool_groups,
                ("native_files", "native_shell"),
            )
            self.assertEqual(cfg.plugin_tool_paths, ())

    def test_tool_group_overlap_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            payload["run"]["tool_groups"] = {
                "enabled": ["native_files", "plugin_local"],
                "disabled": ["plugin_local"],
            }
            with self.assertRaisesRegex(ValueError, "overlap"):
                load_config(write_config(root, payload))

    def test_unknown_tool_group_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            payload["run"]["tool_groups"] = {
                "enabled": ["native_files", "remote_marketplace"],
                "disabled": [],
            }
            with self.assertRaisesRegex(ValueError, "Unknown tool group"):
                load_config(write_config(root, payload))

    def test_granular_file_tool_groups_support_read_only_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            payload["run"]["tool_groups"] = {
                "enabled": ["native_file_read", "native_shell"],
                "disabled": [],
            }
            cfg = load_config(write_config(root, payload))
            self.assertEqual(
                cfg.enabled_tool_groups,
                ("native_file_read", "native_shell"),
            )

    def test_granular_file_tool_groups_support_write_enabled_mode(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            payload["run"]["tool_groups"] = {
                "enabled": [
                    "native_file_read",
                    "native_file_write",
                    "native_shell",
                ],
                "disabled": [],
            }
            cfg = load_config(write_config(root, payload))
            self.assertEqual(
                cfg.enabled_tool_groups,
                (
                    "native_file_read",
                    "native_file_write",
                    "native_shell",
                ),
            )

    def test_native_files_group_remains_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            payload["run"]["tool_groups"] = {
                "enabled": ["native_files", "native_shell"],
                "disabled": [],
            }
            cfg = load_config(write_config(root, payload))
            self.assertEqual(
                cfg.enabled_tool_groups,
                ("native_files", "native_shell"),
            )

    def test_duplicate_plugin_tool_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            payload["run"]["tool_plugins"] = {
                "paths": [
                    "workspace/project/plugins",
                    "workspace/project/plugins",
                ],
            }
            with self.assertRaisesRegex(ValueError, "contains duplicates"):
                load_config(write_config(root, payload))

    def test_plugin_tool_paths_are_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            payload["run"]["tool_groups"] = {
                "enabled": ["native_files", "native_shell", "plugin_local"],
                "disabled": [],
            }
            payload["run"]["tool_plugins"] = {
                "paths": ["workspace/project/plugins"],
            }
            cfg = load_config(write_config(root, payload))
            self.assertEqual(
                cfg.enabled_tool_groups,
                ("native_files", "native_shell", "plugin_local"),
            )
            self.assertEqual(
                cfg.plugin_tool_paths,
                ("workspace/project/plugins",),
            )


if __name__ == "__main__":
    unittest.main()
