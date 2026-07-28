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


class ConfigWebResearchSettingsTests(unittest.TestCase):
    def test_default_web_research_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            cfg = load_config(write_config(root, payload))
            self.assertEqual(cfg.web_research_domain_policy, "none")
            self.assertEqual(cfg.web_research_allowed_domains, ())
            self.assertEqual(cfg.web_research_blocked_domains, ())
            self.assertTrue(cfg.web_research_local_fallback)

    def test_web_research_allowlist_policy_loads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            payload["run"]["web_research"] = {
                "domain_policy": "allowlist",
                "allowed_domains": ["docs.pydantic.dev", "example.com"],
                "blocked_domains": [],
                "local_fallback": True,
            }
            cfg = load_config(write_config(root, payload))
            self.assertEqual(cfg.web_research_domain_policy, "allowlist")
            self.assertEqual(
                cfg.web_research_allowed_domains,
                ("docs.pydantic.dev", "example.com"),
            )
            self.assertEqual(cfg.web_research_blocked_domains, ())
            self.assertTrue(cfg.web_research_local_fallback)

    def test_web_research_none_policy_rejects_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            payload["run"]["web_research"] = {
                "domain_policy": "none",
                "allowed_domains": ["docs.pydantic.dev"],
            }
            with self.assertRaisesRegex(ValueError, "domain_policy='none'"):
                load_config(write_config(root, payload))

    def test_web_research_allowlist_requires_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            payload["run"]["web_research"] = {
                "domain_policy": "allowlist",
                "allowed_domains": [],
            }
            with self.assertRaisesRegex(
                ValueError,
                "allowed_domains is required",
            ):
                load_config(write_config(root, payload))

    def test_web_research_denylist_requires_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = _workspace_root(temp_dir)
            payload = base_config(
                project_root="workspace/project",
                mount_work_root="workspace",
            )
            payload["run"]["web_research"] = {
                "domain_policy": "denylist",
                "blocked_domains": [],
            }
            with self.assertRaisesRegex(
                ValueError,
                "blocked_domains is required",
            ):
                load_config(write_config(root, payload))


if __name__ == "__main__":
    unittest.main()
