from __future__ import annotations

# Legacy facade: import paths now resolve through lllars_core.mcp package.
from lllars_core.mcp.preflight import (  # noqa: F401
    _check_model_endpoint,
    _check_mount_writable,
    _load_toolsets_or_error,
    run_mcp_preflight,
    run_startup_preflight,
)
from lllars_core.mcp.model_probe import (  # noqa: F401
    _build_ollama_tags_url,
    _extract_model_names,
    _normalize_model_name,
    _read_model_payload,
)
from lllars_core.mcp.runtime import (  # noqa: F401
    _probe_connectivity_worker,
    _probe_toolsets,
    _truncate_text,
    has_utf8_bom as _has_utf8_bom,
    probe_connectivity_with_hard_timeout,
    probe_stdio_startup_noise as _probe_stdio_startup_noise,
    read_servers as _read_servers,
)

_probe_connectivity_with_hard_timeout = probe_connectivity_with_hard_timeout

SYMBOL_MIGRATION_MAP = {
    "run_startup_preflight": "lllars_core.mcp.preflight.run_startup_preflight",
    "run_mcp_preflight": "lllars_core.mcp.preflight.run_mcp_preflight",
}

__all__ = [
    "SYMBOL_MIGRATION_MAP",
    "_build_ollama_tags_url",
    "_check_model_endpoint",
    "_check_mount_writable",
    "_extract_model_names",
    "_has_utf8_bom",
    "_load_toolsets_or_error",
    "_normalize_model_name",
    "_probe_connectivity_with_hard_timeout",
    "_probe_connectivity_worker",
    "_probe_stdio_startup_noise",
    "_probe_toolsets",
    "_read_model_payload",
    "_read_servers",
    "_truncate_text",
    "run_mcp_preflight",
    "run_startup_preflight",
]
