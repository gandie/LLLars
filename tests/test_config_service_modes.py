from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from config_test_support import default_service_block, write_config
from lllars_core.config import load_config


def _write_precedence_env(root: Path) -> None:
    (root / "runtime.env").write_text(
        "\n".join(
            [
                "SERVICE_PORT=9001",
                "QUEUE_BACKEND=redis",
                "TEST_COMMAND=python env-test.py",
            ]
        ),
        encoding="utf-8",
    )


class ConfigServiceModeTests(unittest.TestCase):
    def test_split_service_only_config_is_supported_without_run_settings(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace").mkdir(parents=True)
            config_path = write_config(
                root, {"service": default_service_block()}
            )
            cfg = load_config(config_path)
            self.assertEqual(cfg.service_mode, "serve")
            self.assertEqual(cfg.model, "")
            self.assertEqual(cfg.provider_url, "")
            self.assertEqual(cfg.project_root, (root / "workspace").resolve())

    def test_env_file_overrides_service_settings_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            (root / "runtime.env").write_text(
                "SERVICE_PORT=9015\nQUEUE_BACKEND=redis", encoding="utf-8"
            )
            payload = {
                "env_file": "runtime.env",
                "service": default_service_block(),
            }
            cfg = load_config(write_config(root, payload))
            self.assertEqual(cfg.service_mode, "serve")
            self.assertEqual(cfg.service_port, 9015)
            self.assertEqual(cfg.queue_backend, "redis")
            self.assertEqual(cfg.run.model, "")
            self.assertEqual(cfg.project_root, (root / "workspace").resolve())
            self.assertIsNone(cfg.test_command)
            self.assertIsNone(cfg.eval_command)

    def test_split_service_and_run_config_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            payload = {
                "service": default_service_block(workers=2),
                "run": {
                    "model": "test-model",
                    "provider_url": "http://localhost:11434",
                    "project_root": "workspace/project",
                    "commands": {},
                    "command_profile": "python-playground",
                },
            }
            cfg = load_config(write_config(root, payload))
            self.assertEqual(cfg.service_mode, "serve")
            self.assertEqual(cfg.service_workers, 2)
            self.assertEqual(cfg.run.model, "test-model")
            self.assertEqual(cfg.run.command_profile, "python-playground")
            self.assertEqual(
                cfg.allowed_shell_commands,
                ("python main.py", "python test.py"),
            )

    def test_split_and_unsupported_root_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            payload = {
                "service": {"mount_work_root": "workspace"},
                "run": {
                    "model": "test-model",
                    "provider_url": "http://localhost:11434",
                    "project_root": "workspace/project",
                    "commands": {},
                    "command_profile": "none",
                },
                "queue_backend": "inmemory",
            }
            with self.assertRaisesRegex(ValueError, "unsupported root keys"):
                load_config(write_config(root, payload))

    def test_precedence_defaults_env_json_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "workspace" / "project").mkdir(parents=True)
            _write_precedence_env(root)
            payload = {
                "env_file": "runtime.env",
                "service": {
                    "mount_work_root": "workspace",
                    "port": 9010,
                    "queue_backend": "inmemory",
                },
                "run": {
                    "model": "test-model",
                    "provider_url": "http://localhost:11434",
                    "project_root": "workspace/project",
                    "commands": {},
                    "command_profile": "none",
                },
            }
            cfg = load_config(
                write_config(root, payload),
                overrides={"service_port": 9020, "queue_backend": "inmemory"},
            )
            self.assertEqual(cfg.service_port, 9001)
            self.assertEqual(cfg.queue_backend, "redis")
            self.assertIsNone(cfg.test_command)


if __name__ == "__main__":
    unittest.main()
