from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydantic_ai import ModelRetry

from lllars_core.agent_builder import _make_allowed_shell_runner
from lllars_core.tools.shell_policy import register_shell_tools


class _ToolCaptureAgent:
    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, fn):
        self.tools[fn.__name__] = fn
        return fn


class AgentBuilderShellExtensionTests(unittest.TestCase):
    def test_allowlisted_shell_runner_accepts_wildcard_patterns(self) -> None:
        cfg = SimpleNamespace(
            allowed_shell_commands=("python *",),
            project_root=Path("."),
            shell_mode="auto",
            shell_override=None,
            command_profile="none",
            test_command=None,
            eval_command=None,
        )
        run_allowed = _make_allowed_shell_runner(cfg)

        with patch(
            "lllars_core.agent_builder.run_shell",
            return_value={"returncode": 0, "stdout": "ok", "stderr": ""},
        ) as run_shell:
            payload = json.loads(run_allowed("python -m pytest -q", 45))

        self.assertEqual(payload["returncode"], 0)
        self.assertEqual(payload["allowlist_match"], "python *")
        run_shell.assert_called_once_with(
            command="python -m pytest -q",
            cwd=cfg.project_root,
            timeout_sec=45,
            shell_mode="auto",
            shell_override=None,
        )

    def test_register_shell_yolo_tool_resolves_type_hints(self) -> None:
        cfg = SimpleNamespace(
            allowed_shell_commands=(),
            test_command=None,
            eval_command=None,
        )
        agent = _ToolCaptureAgent()

        register_shell_tools(
            agent=agent,
            cfg=cfg,
            emit_thought=lambda _message: None,
            tool_error=lambda _tool, message, _hint: message,
            run_allowed_shell=lambda _cmd, _timeout: "{}",
            run_unrestricted_shell=lambda _cmd, _timeout: "{}",
        )

        self.assertIn("run_unrestricted_shell", agent.tools)

    def test_run_allowlisted_shell_invalid_id_raises_model_retry(self) -> None:
        cfg = SimpleNamespace(
            allowed_shell_commands=("echo ok",),
            test_command=None,
            eval_command=None,
        )
        agent = _ToolCaptureAgent()
        errors: list[str] = []

        register_shell_tools(
            agent=agent,
            cfg=cfg,
            emit_thought=lambda _message: None,
            tool_error=lambda _tool, message, _hint: errors.append(message)
            or message,
            run_allowed_shell=lambda _cmd, _timeout: "{}",
        )

        tool = agent.tools["run_allowlisted_shell"]
        with self.assertRaises(ModelRetry):
            tool(None, command_id=2)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
