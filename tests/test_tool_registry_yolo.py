from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydantic_ai import Agent

from lllars_core.tools.registry import register_runtime_tools


class RuntimeToolRegistryYoloTests(unittest.TestCase):
    def test_register_runtime_tools_supports_native_shell_yolo_group(
        self,
    ) -> None:
        cfg = SimpleNamespace(
            enabled_tool_groups=("native_shell_yolo",),
            plugin_tool_paths=(),
            project_root=Path("."),
            allowed_shell_commands=(),
            test_command=None,
            eval_command=None,
        )
        agent: Agent[object, str] = Agent("test")

        with patch(
            "lllars_core.tools.registry_shell_groups.register_shell_tools"
        ) as register_shell:
            register_runtime_tools(
                agent=agent,
                cfg=cfg,
                emit_thought=lambda _message: None,
                tool_error=lambda _tool, message, _hint: message,
                run_allowed_shell=lambda _cmd, _timeout: "{}",
                run_unrestricted_shell=lambda _cmd, _timeout: "{}",
            )

        register_shell.assert_called_once()


if __name__ == "__main__":
    unittest.main()
