from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydantic_ai import Agent
from pydantic_ai import ModelRetry

from lllars_core.agent_builder import (
    _make_allowed_shell_runner,
    _normalize_provider_base_url,
    _resolve_model_spec,
    make_agent_deps,
)
from lllars_core.shell import ShellSelection
from lllars_core.tools.native import register_file_tools
from lllars_core.tools.shell_policy import register_shell_tools


class AgentBuilderShellRunnerTests(unittest.TestCase):
    def test_allowlisted_shell_runner_uses_shell_policy(self) -> None:
        cfg = SimpleNamespace(
            allowed_shell_commands=("python test.py",),
            project_root=Path("."),
            shell_mode="auto",
            shell_override=None,
            command_profile="none",
            test_command="python test.py",
            eval_command=None,
        )
        run_allowed = _make_allowed_shell_runner(cfg)

        with patch(
            "lllars_core.agent_builder.run_shell",
            return_value={"returncode": 0, "stdout": "ok", "stderr": ""},
        ) as run_shell:
            payload = json.loads(run_allowed("python test.py", 45))

        self.assertEqual(payload["returncode"], 0)
        run_shell.assert_called_once_with(
            command="python test.py",
            cwd=cfg.project_root,
            timeout_sec=45,
            shell_mode="auto",
            shell_override=None,
        )

    def test_make_agent_deps_uses_detected_shell_name(self) -> None:
        cfg = SimpleNamespace(
            project_root=Path("."),
            shell_mode="auto",
            shell_override=None,
            command_profile="none",
            allowed_shell_commands=(),
            test_command=None,
            eval_command=None,
        )

        with patch(
            "lllars_core.agent_builder.detect_shell",
            return_value=ShellSelection(
                name="bash",
                executable="bash",
                command_prefix=("-lc",),
            ),
        ):
            deps = make_agent_deps(cfg)

        self.assertEqual(deps.shell_name, "bash")


class AgentBuilderToolRegistrationRegressionTests(unittest.TestCase):
    def test_register_file_tools_resolves_type_hints(self) -> None:
        cfg = SimpleNamespace(project_root=Path("."))
        agent: Agent[object, str] = Agent("test")

        # Regression guard: @agent.tool must not fail while evaluating
        # RunContext[AgentDeps] annotations.
        register_file_tools(
            agent=agent,
            cfg=cfg,
            tool_error=lambda _tool, message, _hint: message,
        )

    def test_register_shell_tools_resolves_type_hints(self) -> None:
        cfg = SimpleNamespace(
            allowed_shell_commands=("echo ok",),
            test_command="echo ok",
            eval_command="echo ok",
        )
        agent: Agent[object, str] = Agent("test")

        # Regression guard: all shell-related tools should register without
        # NameError from postponed annotation evaluation.
        register_shell_tools(
            agent=agent,
            cfg=cfg,
            emit_thought=lambda _message: None,
            tool_error=lambda _tool, message, _hint: message,
            run_allowed_shell=lambda _cmd, _timeout: "{}",
        )


class _ToolCaptureAgent:
    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, fn):
        self.tools[fn.__name__] = fn
        return fn


class ShellToolRetryPropagationTests(unittest.TestCase):
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

    def test_run_test_command_propagates_model_retry(self) -> None:
        cfg = SimpleNamespace(
            allowed_shell_commands=(),
            test_command="echo ok",
            eval_command=None,
        )
        agent = _ToolCaptureAgent()

        register_shell_tools(
            agent=agent,
            cfg=cfg,
            emit_thought=lambda _message: None,
            tool_error=lambda _tool, message, _hint: message,
            run_allowed_shell=lambda _cmd, _timeout: (_ for _ in ()).throw(
                ModelRetry("Please retry")
            ),
        )

        tool = agent.tools["run_test_command"]
        with self.assertRaises(ModelRetry):
            tool(None)


class AgentBuilderModelSpecResolutionTests(unittest.TestCase):
    def test_explicit_provider_prefix_is_preserved(self) -> None:
        self.assertEqual(
            _resolve_model_spec("openai:gpt-4o-mini"),
            "openai:gpt-4o-mini",
        )

    def test_unprefixed_model_defaults_to_ollama_prefix(self) -> None:
        self.assertEqual(
            _resolve_model_spec("qwen2.5-coder:7b"),
            "ollama:qwen2.5-coder:7b",
        )

    def test_empty_model_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "model is empty"):
            _resolve_model_spec("   ")


class AgentBuilderProviderUrlNormalizationTests(unittest.TestCase):
    def test_ollama_url_appends_v1_when_missing(self) -> None:
        self.assertEqual(
            _normalize_provider_base_url("ollama", "http://localhost:11434"),
            "http://localhost:11434/v1",
        )

    def test_ollama_url_preserves_existing_v1(self) -> None:
        self.assertEqual(
            _normalize_provider_base_url(
                "ollama",
                "http://localhost:11434/v1",
            ),
            "http://localhost:11434/v1",
        )

    def test_non_ollama_url_is_not_rewritten(self) -> None:
        self.assertEqual(
            _normalize_provider_base_url("openai", "https://api.openai.com"),
            "https://api.openai.com",
        )


if __name__ == "__main__":
    unittest.main()
