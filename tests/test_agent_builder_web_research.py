from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from pydantic_ai.capabilities import WebFetch
from pydantic_ai.capabilities import WebSearch
from pydantic_ai.native_tools import WebSearchTool
from pydantic_ai.tools import Tool

from lllars_core.agent_builder import _build_capabilities


class AgentBuilderWebResearchCapabilityTests(unittest.TestCase):
    def _cfg(
        self,
        *,
        enabled_tool_groups: tuple[str, ...],
        network_policy: str,
        allowed_domains: tuple[str, ...] = (),
        blocked_domains: tuple[str, ...] = (),
        local_fallback: bool = True,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            enabled_tool_groups=enabled_tool_groups,
            network_policy=network_policy,
            web_research_allowed_domains=allowed_domains,
            web_research_blocked_domains=blocked_domains,
            web_research_local_fallback=local_fallback,
            skills_enabled=False,
            skills_glob="",
            skills_defer_loading=False,
            skills_require_description=True,
            project_root=Path("."),
        )

    def test_web_research_capabilities_enabled_when_group_and_online(
        self,
    ) -> None:
        cfg = self._cfg(
            enabled_tool_groups=("native_shell", "native_web_research"),
            network_policy="inherit",
        )
        capabilities = _build_capabilities(cfg)
        web_search = [
            cap for cap in capabilities if isinstance(cap, WebSearch)
        ]
        web_fetch = [cap for cap in capabilities if isinstance(cap, WebFetch)]
        self.assertEqual(len(web_search), 1)
        self.assertEqual(len(web_fetch), 1)

    def test_web_research_capabilities_skipped_when_group_disabled(
        self,
    ) -> None:
        cfg = self._cfg(
            enabled_tool_groups=("native_shell",),
            network_policy="inherit",
        )
        capabilities = _build_capabilities(cfg)
        self.assertFalse(
            any(isinstance(cap, WebSearch) for cap in capabilities)
        )
        self.assertFalse(
            any(isinstance(cap, WebFetch) for cap in capabilities)
        )

    def test_web_research_capabilities_skipped_when_offline(self) -> None:
        cfg = self._cfg(
            enabled_tool_groups=("native_web_research",),
            network_policy="offline",
        )
        capabilities = _build_capabilities(cfg)
        self.assertFalse(
            any(isinstance(cap, WebSearch) for cap in capabilities)
        )
        self.assertFalse(
            any(isinstance(cap, WebFetch) for cap in capabilities)
        )

    def test_web_search_keeps_fallback_when_domain_filtering_enabled(
        self,
    ) -> None:
        cfg = self._cfg(
            enabled_tool_groups=("native_web_research",),
            network_policy="inherit",
            allowed_domains=("docs.pydantic.dev",),
            blocked_domains=(),
            local_fallback=True,
        )
        capabilities = _build_capabilities(cfg)
        web_search = next(
            cap for cap in capabilities if isinstance(cap, WebSearch)
        )

        self.assertIsInstance(web_search.native, WebSearchTool)
        self.assertEqual(
            web_search.native.allowed_domains,
            ["docs.pydantic.dev"],
        )
        self.assertIsInstance(web_search.local, Tool)
        self.assertFalse(web_search._requires_native())


if __name__ == "__main__":
    unittest.main()
