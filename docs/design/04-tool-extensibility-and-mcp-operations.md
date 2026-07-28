# Tool Extensibility and MCP Capability Operations

This chapter describes shipped operator semantics for configurable tool
registration and capability-aware MCP behavior.

## Tool Taxonomy and Execution Boundaries
- `native_files`: backward-compatible alias for full built-in local file tools
  (`list_files`, `read_file`, `write_file`) scoped to `project_root`.
- `native_file_read`: built-in read-only local file tools
  (`list_files`, `read_file`) scoped to `project_root`.
- `native_file_write`: built-in local file write tool (`write_file`) scoped to
  `project_root`.
- `native_shell`: built-in policy-gated shell tools (test/eval/allowlisted
  shell execution).
- `plugin_local`: local repository plugin tools loaded from configured local
  paths only.
- `mcp_toolsets`: remote MCP-backed tools loaded from configured MCP servers.
- Group selection controls registration only and does not widen safety policy.

## Tool-Group Config Schema
```json
{"run": {"tool_groups": {"enabled": ["native_file_read", "native_shell", "plugin_local", "mcp_toolsets"], "disabled": []}}}
```

Validation rules:
- Unknown group names are configuration errors.
- Duplicate values within one list are configuration errors.
- If the same group appears in both `enabled` and `disabled`, configuration is
  rejected (conflict error).
- Omitted `tool_groups` defaults to `native_files` + `native_shell`.
- `native_files` remains supported as a migration-safe compatibility alias.
- Plugin sources are configured via `run.tool_plugins.paths` (local paths
  only).

## MCP Capability Matrix and Fallback Policy
Capability states:
- `healthy`: required server fields are present and connectivity probe succeeds.
- `degraded`: configuration is parseable but one or more capability checks
  fail.
- `unavailable`: required server launch contract is missing or connectivity
  cannot be established.

Fallback policy:
- Default policy is degraded-continue.
- If at least one configured MCP server is healthy, runtime continues with
  healthy capabilities and warns for degraded/unavailable servers.
- If no configured MCP servers are healthy, MCP capability is unavailable and
  runtime falls back to native/plugin groups only.
- If capability negotiation fails, startup falls back to legacy connectivity
  probing and emits warning lines.
- Startup diagnostics include aggregate and per-server capability lines.
- MCP toolset loading is currently gated by `run.mcp_enabled` and
  `run.mcp_config_path`.
- `mcp_toolsets` remains a stable group identifier for migration
  compatibility.

## Operator Migration Summary
- Legacy baseline: fixed native registration with implicit MCP behavior.
- Current baseline: explicit `tool_groups`, optional local plugin paths,
  capability-aware MCP degraded continuation.
- Operators can disable MCP fully with `mcp_enabled=false` while retaining
  native/plugin functionality.
