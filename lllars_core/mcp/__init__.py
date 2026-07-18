from __future__ import annotations

from lllars_core.mcp.loader import load_toolsets_from_mcp_config
from lllars_core.mcp.preflight import run_mcp_preflight, run_startup_preflight

SYMBOL_MIGRATION_MAP = {
    "load_toolsets_from_mcp_config": (
        "lllars_core.mcp.loader.load_toolsets_from_mcp_config"
    ),
    "run_mcp_preflight": "lllars_core.mcp.preflight.run_mcp_preflight",
    "run_startup_preflight": "lllars_core.mcp.preflight.run_startup_preflight",
}

__all__ = [
    "SYMBOL_MIGRATION_MAP",
    "load_toolsets_from_mcp_config",
    "run_mcp_preflight",
    "run_startup_preflight",
]
