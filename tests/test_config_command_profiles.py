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


def _profile_payload(root: Path, source_name: str, profile_name: str) -> dict:
    payload = base_config(
        project_root="workspace/project",
        mount_work_root="workspace",
    )
    payload["run"]["command_profile"] = profile_name
    payload["run"]["command_profiles_path"] = source_name
    return payload


class ConfigCommandProfileTests(unittest.TestCase):
    def test_external_command_profile_is_loaded_from_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            (root / "profiles.json").write_text(
                '{"lint-only": ["python -m pytest -q"]}',
                encoding="utf-8",
            )
            payload = _profile_payload(root, "profiles.json", "lint-only")
            cfg = load_config(write_config(root, payload))
            self.assertEqual(cfg.command_profile, "lint-only")
            self.assertEqual(cfg.allowed_shell_commands, ("python -m pytest -q",))

    def test_external_command_profile_is_loaded_from_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            (root / "profiles.yaml").write_text(
                "profiles:\n  lint-only:\n    - python -m pytest -q\n",
                encoding="utf-8",
            )
            payload = _profile_payload(root, "profiles.yaml", "lint-only")
            cfg = load_config(write_config(root, payload))
            self.assertEqual(cfg.command_profile, "lint-only")
            self.assertEqual(cfg.allowed_shell_commands, ("python -m pytest -q",))

    def test_external_profile_conflicting_with_builtin_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            (root / "profiles.json").write_text(
                '{"python-playground": ["python -m pytest -q"]}',
                encoding="utf-8",
            )
            payload = _profile_payload(
                root,
                "profiles.json",
                "python-playground",
            )
            with self.assertRaisesRegex(
                ValueError,
                "conflicts with built-in profile",
            ):
                load_config(write_config(root, payload))

    def test_unknown_profile_diagnostic_includes_external_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            (root / "profiles.json").write_text(
                '{"lint-only": ["python -m pytest -q"]}',
                encoding="utf-8",
            )
            payload = _profile_payload(root, "profiles.json", "does-not-exist")
            with self.assertRaisesRegex(ValueError, "command_profiles_path"):
                load_config(write_config(root, payload))


if __name__ == "__main__":
    unittest.main()
