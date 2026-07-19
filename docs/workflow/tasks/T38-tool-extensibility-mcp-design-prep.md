# T38 Tool Extensibility and MCP Design Prep

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

## Objective
Define architecture for configurable native tools, plugin tools, and MCP capability handling.

## Scope
- Tool taxonomy and execution boundaries.
- Config schema draft for tool-group enable/disable.
- MCP capability matrix and fallback policy.

## Non-Goals
- No plugin runtime implementation.
- No capability negotiation code.

## Target Files
- docs/DESIGN.md
- docs/workflow/tasks/T38-tool-extensibility-mcp-design-prep.md
- lllars_core/tools/registry.py
- lllars_core/mcp/runtime.py

## Verification
- Design review against `tools/` and `mcp/` package seams.

## Rollback
Keep fixed wiring and treat design as draft until T39 and T40 land.

## Completion Artifact
Approved design checklist for T39 and T40.
