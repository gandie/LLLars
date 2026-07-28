from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydantic_ai import Agent

from lllars_core.tools.registry import register_runtime_tools


class RuntimeFileToolGroupSelectionTests(unittest.TestCase):
    def _cfg(self, groups: tuple[str, ...]) -> SimpleNamespace:
        return SimpleNamespace(
            enabled_tool_groups=groups,
            plugin_tool_paths=(),
            project_root=Path("."),
            allowed_shell_commands=(),
            test_command=None,
            eval_command=None,
        )

    def _run_with_groups(
        self,
        groups: tuple[str, ...],
    ) -> tuple[int, int, int, int]:
        agent: Agent[object, str] = Agent("test")
        cfg = self._cfg(groups)

        with (
            patch(
                "lllars_core.tools.registry.register_file_read_tools"
            ) as register_files_read,
            patch(
                "lllars_core.tools.registry.register_file_write_tools"
            ) as register_files_write,
            patch("lllars_core.tools.registry.register_shell_tools") as register_shell,
            patch(
                "lllars_core.tools.registry.register_local_plugin_tools"
            ) as register_plugins,
        ):
            register_runtime_tools(
                agent=agent,
                cfg=cfg,
                emit_thought=lambda _message: None,
                tool_error=lambda _tool, message, _hint: message,
                run_allowed_shell=lambda _cmd, _timeout: "{}",
            )
            return (
                register_files_read.call_count,
                register_files_write.call_count,
                register_shell.call_count,
                register_plugins.call_count,
            )

    def test_read_only_group_registers_only_read_tools(self) -> None:
        counts = self._run_with_groups(("native_file_read",))
        self.assertEqual(counts, (1, 0, 0, 0))

    def test_write_enabled_groups_register_read_and_write_tools(
        self,
    ) -> None:
        counts = self._run_with_groups(
            ("native_file_read", "native_file_write")
        )
        self.assertEqual(counts, (1, 1, 0, 0))

    def test_native_files_alias_does_not_duplicate_registrations(
        self,
    ) -> None:
        counts = self._run_with_groups(
            ("native_files", "native_file_read", "native_file_write")
        )
        self.assertEqual(counts, (1, 1, 0, 0))


if __name__ == "__main__":
    unittest.main()
