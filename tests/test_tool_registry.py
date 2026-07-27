from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydantic_ai import Agent

from lllars_core.tools.plugins import register_local_plugin_tools
from lllars_core.tools.registry import register_runtime_tools


class RuntimeToolRegistrySelectionTests(unittest.TestCase):
    def test_register_runtime_tools_respects_enabled_groups(self) -> None:
        cfg = SimpleNamespace(
            enabled_tool_groups=("native_shell",),
            plugin_tool_paths=(),
            project_root=Path("."),
            allowed_shell_commands=("echo ok",),
            test_command=None,
            eval_command=None,
        )
        agent: Agent[object, str] = Agent("test")

        with (
            patch(
                "lllars_core.tools.registry.register_file_tools"
            ) as register_files,
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

        register_files.assert_not_called()
        register_plugins.assert_not_called()
        register_shell.assert_called_once()

    def test_register_runtime_tools_loads_local_plugin_group(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plugin_file = root / "plugins" / "sample_plugin.py"
            plugin_file.parent.mkdir(parents=True)
            plugin_file.write_text(
                "def register_tools(agent, cfg, tool_error):\n"
                "    @agent.tool\n"
                "    def hello_runtime_plugin(ctx):\n"
                "        _ = (ctx, cfg, tool_error)\n"
                "        return 'ok'\n",
                encoding="utf-8",
            )
            cfg = SimpleNamespace(
                enabled_tool_groups=("plugin_local",),
                plugin_tool_paths=("plugins",),
                project_root=root,
                allowed_shell_commands=(),
                test_command=None,
                eval_command=None,
            )
            agent = _FakeAgent()

            register_runtime_tools(
                agent=agent,
                cfg=cfg,
                emit_thought=lambda _message: None,
                tool_error=lambda _tool, message, _hint: message,
                run_allowed_shell=lambda _cmd, _timeout: "{}",
            )

            self.assertIn("hello_runtime_plugin", agent.tools)


class _FakeAgent:
    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, fn):
        self.tools[fn.__name__] = fn
        return fn


class LocalPluginToolLoadingTests(unittest.TestCase):
    def test_register_local_plugin_tools_registers_plugin_tool(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plugin_file = root / "plugins" / "sample_plugin.py"
            plugin_file.parent.mkdir(parents=True)
            plugin_file.write_text(
                "def register_tools(agent, cfg, tool_error):\n"
                "    @agent.tool\n"
                "    def hello_plugin(ctx):\n"
                "        _ = (ctx, cfg, tool_error)\n"
                "        return 'ok'\n",
                encoding="utf-8",
            )
            cfg = SimpleNamespace(
                project_root=root,
                plugin_tool_paths=("plugins/sample_plugin.py",),
            )
            agent = _FakeAgent()

            register_local_plugin_tools(
                agent=agent,
                cfg=cfg,
                tool_error=lambda _tool, message, _hint: message,
            )

            self.assertIn("hello_plugin", agent.tools)

    def test_register_local_plugin_tools_registers_from_directory(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plugin_file = root / "plugins" / "sample_plugin.py"
            plugin_file.parent.mkdir(parents=True)
            plugin_file.write_text(
                "def register_tools(agent, cfg, tool_error):\n"
                "    @agent.tool\n"
                "    def hello_from_directory(ctx):\n"
                "        _ = (ctx, cfg, tool_error)\n"
                "        return 'ok'\n",
                encoding="utf-8",
            )
            cfg = SimpleNamespace(
                project_root=root,
                plugin_tool_paths=("plugins",),
            )
            agent = _FakeAgent()

            register_local_plugin_tools(
                agent=agent,
                cfg=cfg,
                tool_error=lambda _tool, message, _hint: message,
            )

            self.assertIn("hello_from_directory", agent.tools)

    def test_register_local_plugin_tools_rejects_missing_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cfg = SimpleNamespace(
                project_root=root,
                plugin_tool_paths=("plugins/missing.py",),
            )
            with self.assertRaisesRegex(ValueError, "Plugin path not found"):
                register_local_plugin_tools(
                    agent=_FakeAgent(),
                    cfg=cfg,
                    tool_error=lambda _tool, message, _hint: message,
                )

    def test_register_local_plugin_tools_rejects_unsafe_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside_dir = root.parent / "outside"
            outside_dir.mkdir(exist_ok=True)
            outside_path = outside_dir / "plugin.py"
            outside_path.write_text("x = 1\n", encoding="utf-8")
            cfg = SimpleNamespace(
                project_root=root,
                plugin_tool_paths=(str(outside_path),),
            )
            with self.assertRaisesRegex(ValueError, "Unsafe plugin path"):
                register_local_plugin_tools(
                    agent=_FakeAgent(),
                    cfg=cfg,
                    tool_error=lambda _tool, message, _hint: message,
                )

    def test_register_local_plugin_tools_rejects_duplicate_modules(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plugin_file = root / "plugins" / "sample_plugin.py"
            plugin_file.parent.mkdir(parents=True)
            plugin_file.write_text(
                "def register_tools(agent, cfg, tool_error):\n"
                "    return None\n",
                encoding="utf-8",
            )
            cfg = SimpleNamespace(
                project_root=root,
                plugin_tool_paths=("plugins", "plugins/sample_plugin.py"),
            )
            with self.assertRaisesRegex(ValueError, "Duplicate plugin module"):
                register_local_plugin_tools(
                    agent=_FakeAgent(),
                    cfg=cfg,
                    tool_error=lambda _tool, message, _hint: message,
                )


if __name__ == "__main__":
    unittest.main()
