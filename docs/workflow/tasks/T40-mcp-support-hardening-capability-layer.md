# T40 MCP Support Hardening and Capability Layer

## Metadata
- Status: Proposed
- Priority: P1
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

## Objective
Add capability-aware startup checks and runtime degradation behavior.

## Scope
- Capability negotiation summary in startup diagnostics.
- Structured degraded-mode behavior for partial MCP capability.
- Clear warnings for unavailable capability sets.

## Non-Goals
- No MCP protocol extensions.
- No provider-specific capability hardcoding.

## Target Files
- lllars_core/mcp/capabilities.py
- lllars_core/mcp/runtime.py
- lllars_core/mcp/preflight.py
- lllars_core/agent_builder.py
- tests/test_cli_regression.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_cli_regression.py"
- .\\venv\\Scripts\\python.exe .\\lllars.py --config .\\playground.example.json --prompt "mcp capability smoke"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"

## Rollback
Keep current preflight-only behavior as fallback.

## Completion Artifact
Startup/runtime traces proving capability-aware degradation.
