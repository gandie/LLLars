from __future__ import annotations

import platform

from lllars_core.config.loader import load_config
from lllars_core.config.models import (
    DEFAULT_AGENT_RETRIES_OUTPUT,
    DEFAULT_AGENT_RETRIES_TOOLS,
    DEFAULT_COMMAND_PROFILE,
    DEFAULT_CONFIG_PATH,
    DEFAULT_MCP_INIT_TIMEOUT_SEC,
    DEFAULT_NETWORK_POLICY,
    DEFAULT_QUEUE_BACKEND,
    DEFAULT_SERVICE_HOST,
    DEFAULT_SERVICE_MODE,
    DEFAULT_SERVICE_PORT,
    DEFAULT_SERVICE_WORKERS,
    DEFAULT_SHELL_MODE,
    DEFAULT_TIMEOUT_SEC,
    DEFAULT_TOOL_TIMEOUT_SEC,
    DEFAULT_USAGE_TOOL_CALLS_LIMIT,
    POSIX_SHELLS,
    ROOT,
    VALID_NETWORK_POLICIES,
    VALID_QUEUE_BACKENDS,
    VALID_SERVICE_MODES,
    VALID_SHELL_MODES,
    VALID_SHELL_OVERRIDES,
    WINDOWS_SHELLS,
    HarnessConfig,
    RunConfig,
    ServiceConfig,
)
from lllars_core.config.tools_section import (
    COMMAND_PROFILE_REGISTRY,
    build_default_tool_policy,
    canonicalize_shell_command,
)

SYMBOL_MIGRATION_MAP = {
    "load_config": "lllars_core.config.loader.load_config",
    "HarnessConfig": "lllars_core.config.models.HarnessConfig",
    "RunConfig": "lllars_core.config.models.RunConfig",
    "ServiceConfig": "lllars_core.config.models.ServiceConfig",
    "COMMAND_PROFILE_REGISTRY": (
        "lllars_core.config.tools_section.COMMAND_PROFILE_REGISTRY"
    ),
    "canonicalize_shell_command": (
        "lllars_core.config.tools_section.canonicalize_shell_command"
    ),
    "build_default_tool_policy": (
        "lllars_core.config.tools_section.build_default_tool_policy"
    ),
}

__all__ = [
    "COMMAND_PROFILE_REGISTRY",
    "DEFAULT_AGENT_RETRIES_OUTPUT",
    "DEFAULT_AGENT_RETRIES_TOOLS",
    "DEFAULT_COMMAND_PROFILE",
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_MCP_INIT_TIMEOUT_SEC",
    "DEFAULT_NETWORK_POLICY",
    "DEFAULT_QUEUE_BACKEND",
    "DEFAULT_SERVICE_HOST",
    "DEFAULT_SERVICE_MODE",
    "DEFAULT_SERVICE_PORT",
    "DEFAULT_SERVICE_WORKERS",
    "DEFAULT_SHELL_MODE",
    "DEFAULT_TIMEOUT_SEC",
    "DEFAULT_TOOL_TIMEOUT_SEC",
    "DEFAULT_USAGE_TOOL_CALLS_LIMIT",
    "HarnessConfig",
    "POSIX_SHELLS",
    "ROOT",
    "RunConfig",
    "SYMBOL_MIGRATION_MAP",
    "ServiceConfig",
    "VALID_NETWORK_POLICIES",
    "VALID_QUEUE_BACKENDS",
    "VALID_SERVICE_MODES",
    "VALID_SHELL_MODES",
    "VALID_SHELL_OVERRIDES",
    "WINDOWS_SHELLS",
    "build_default_tool_policy",
    "canonicalize_shell_command",
    "load_config",
    "platform",
]
