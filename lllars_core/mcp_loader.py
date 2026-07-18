from __future__ import annotations

# Legacy facade: import paths now resolve through lllars_core.mcp package.
from lllars_core.mcp.loader import (  # noqa: F401
    _load_config,
    load_toolsets_from_mcp_config,
)

SYMBOL_MIGRATION_MAP = {
    "load_toolsets_from_mcp_config": (
        "lllars_core.mcp.loader.load_toolsets_from_mcp_config"
    ),
}

__all__ = [
    "SYMBOL_MIGRATION_MAP",
    "_load_config",
    "load_toolsets_from_mcp_config",
]
