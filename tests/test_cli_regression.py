from __future__ import annotations

import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from runtime_api_smoke_test import main
from lllars_core.agent_builder import _load_mcp_toolsets
from lllars_core.mcp.preflight import run_mcp_preflight


class RuntimeApiSmokeCliRegressionTests(unittest.TestCase):
    def test_main_normalizes_expected_shells(self) -> None:
        with (
            patch.object(
                sys,
                "argv",
                [
                    "runtime_api_smoke_test.py",
                    "--expected-shells",
                    " bash, SH , pwsh ",
                ],
            ),
            patch(
                "runtime_api_smoke_test.run_smoke_test",
                return_value=0,
            ) as run_smoke,
        ):
            with self.assertRaises(SystemExit) as exit_ctx:
                main()

        self.assertEqual(exit_ctx.exception.code, 0)
        self.assertEqual(
            run_smoke.call_args.kwargs["expected_shells"],
            ("bash", "sh", "pwsh"),
        )

    def test_main_rejects_empty_expected_shells(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "runtime_api_smoke_test.py",
                "--expected-shells",
                " , , ",
            ],
        ):
            with self.assertRaisesRegex(
                SystemExit,
                "--expected-shells must include at least one shell",
            ):
                main()


class McpCapabilityLayerRegressionTests(unittest.TestCase):
    _subset_payload: str
    _RUNTIME_SERVERS = {
        "healthy": {
            "command": "node",
            "args": ["healthy.js"],
        },
        "broken": {"command": "node", "args": ["broken.js"]},
    }

    def _cfg(self) -> SimpleNamespace:
        return SimpleNamespace(
            mcp_enabled=True,
            mcp_config_path=SimpleNamespace(),
            mcp_init_timeout_sec=2.0,
        )

    def _run_preflight(
        self,
        servers: dict[str, dict],
        *,
        probe_result: tuple[bool, str] | None = None,
        probe_side_effect=None,
    ) -> tuple[bool, list[str]]:
        cfg = self._cfg()
        with (
            patch(
                "lllars_core.mcp.preflight.read_servers",
                return_value=(servers, None),
            ),
            patch(
                "lllars_core.mcp.preflight.has_utf8_bom",
                return_value=False,
            ),
            patch(
                (
                    "lllars_core.mcp.preflight."
                    "probe_server_connectivity_with_hard_timeout"
                ),
                return_value=probe_result,
                side_effect=probe_side_effect,
            ),
        ):
            return run_mcp_preflight(cfg)

    def _agent_cfg(self) -> SimpleNamespace:
        return SimpleNamespace(
            mcp_enabled=True,
            mcp_config_path=SimpleNamespace(),
            mcp_init_timeout_sec=3.0,
        )

    def _capture_subset_toolsets(
        self,
        *,
        mcp_config_path,
        init_timeout_sec,
    ) -> list[str]:
        self.assertEqual(init_timeout_sec, 3.0)
        self._subset_payload = mcp_config_path.read_text(encoding="utf-8")
        return ["toolset-healthy"]

    def _load_agent_toolsets_with_capabilities(
        self,
        cfg: SimpleNamespace,
        thoughts: list[str],
    ) -> list[object]:
        with (
            patch(
                "lllars_core.mcp.runtime_capability.read_servers",
                return_value=(self._RUNTIME_SERVERS, None),
            ),
            patch(
                (
                    "lllars_core.mcp.runtime_capability."
                    "probe_server_connectivity_with_hard_timeout"
                ),
                side_effect=lambda name, *_args, **_kwargs: (
                    (True, "ok") if name == "healthy" else (False, "bad")
                ),
            ),
            patch(
                (
                    "lllars_core.mcp.runtime_capability."
                    "load_toolsets_from_mcp_config"
                ),
                side_effect=self._capture_subset_toolsets,
            ),
        ):
            return _load_mcp_toolsets(cfg, thoughts.append)

    def test_preflight_continues_with_partial_healthy_capabilities(
        self,
    ) -> None:
        ok, lines = self._run_preflight(
            {
                "healthy": {"command": "node", "args": ["ok.js"]},
                "missing": {},
            },
            probe_side_effect=lambda name, *_args, **_kwargs: (
                (True, "ok") if name == "healthy" else (False, "bad")
            ),
        )

        self.assertTrue(ok)
        joined = "\n".join(lines)
        self.assertIn("mcp_capabilities: healthy=1", joined)
        self.assertIn(
            "warning: unavailable MCP capability sets: missing",
            joined,
        )
        self.assertIn(
            "mcp_degraded_mode: continuing with healthy MCP capability sets",
            joined,
        )

    def test_preflight_continues_when_no_healthy_capabilities(self) -> None:
        ok, lines = self._run_preflight(
            {
                "unreachable": {
                    "command": "node",
                    "args": ["server.js"],
                }
            },
            probe_result=(False, "connection failed"),
        )

        self.assertTrue(ok)
        self.assertIn(
            "warning: no healthy MCP capability sets; "
            "continuing with native/plugin tools only",
            "\n".join(lines),
        )

    def test_agent_builder_loads_only_healthy_server_toolsets(self) -> None:
        cfg = self._agent_cfg()
        thoughts: list[str] = []
        toolsets = self._load_agent_toolsets_with_capabilities(cfg, thoughts)

        self.assertIn('"healthy"', self._subset_payload)
        self.assertNotIn('"broken"', self._subset_payload)
        self.assertEqual(toolsets, ["toolset-healthy"])
        self.assertTrue(
            any(
                "warning: unavailable MCP capability sets" in item
                for item in thoughts
            )
        )


if __name__ == "__main__":
    unittest.main()
