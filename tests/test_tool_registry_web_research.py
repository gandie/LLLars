from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydantic_ai import Agent

from lllars_core.tools.registry import register_runtime_tools


def _web_research_cfg() -> SimpleNamespace:
    return SimpleNamespace(
        enabled_tool_groups=("native_web_research",),
        plugin_tool_paths=(),
        project_root=Path("."),
        allowed_shell_commands=(),
        test_command=None,
        eval_command=None,
    )


class RuntimeWebResearchToolGroupTests(unittest.TestCase):
    def test_register_runtime_tools_accepts_web_research_group(self) -> None:
        cfg = _web_research_cfg()
        agent: Agent[object, str] = Agent("test")

        with (
            patch(
                "lllars_core.tools.registry.register_file_read_tools"
            ) as register_files_read,
            patch(
                "lllars_core.tools.registry.register_file_write_tools"
            ) as register_files_write,
            patch(
                "lllars_core.tools.registry.register_shell_tools"
            ) as register_shell,
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

        register_files_read.assert_not_called()
        register_files_write.assert_not_called()
        register_shell.assert_not_called()
        register_plugins.assert_not_called()


if __name__ == "__main__":
    unittest.main()
