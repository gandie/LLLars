---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-07-27
  verdict: accepted
  would_delegate_similar_again: true

  score_scale:
    min: 1
    max: 5
    meaning:
      1: poor
      3: acceptable
      5: excellent

  outcome:
    correctness: 3
    scope_discipline: 4
    validation_trust: 3

  collaboration:
    ambiguity_handling: 3
    operator_load: 3
    trust_delta: 3

  notes: >
    Agent fucked YAML frontmatter again. Implementation seems sound.
---

# T40 MCP Support Hardening and Capability Layer

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-27

## Why Needed
MCP startup/runtime behavior was all-or-nothing, which caused unnecessary
startup failures when only part of configured MCP capability was unavailable.
T40 is needed to introduce capability-aware diagnostics and degraded-continue
runtime behavior while preserving a legacy fallback path.

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
- lllars_core/mcp/runtime_capability.py
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

## Completion Notes
- Added capability-layer module with per-server capability classification,
	negotiation, and structured summary/warning rendering.
- Updated preflight MCP path to emit capability negotiation diagnostics,
	continue in degraded mode when healthy capability remains, continue with
	native/plugin-only fallback when no healthy MCP capability remains, and keep
	legacy connectivity probe behavior as fallback on negotiation failure.
- Added per-server connectivity probing helper that stages single-server MCP
	configs for isolated capability checks.
- Extracted runtime MCP toolset loading into capability-aware loader that keeps
	only healthy MCP servers for runtime toolset registration and emits warnings
	for degraded/unavailable sets.
- Added CLI regression coverage for degraded-mode preflight continuation and
	healthy-subset runtime MCP toolset selection.
- Validation results:
	- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_cli_regression.py"`
	- PASS `.\venv\Scripts\python.exe .\lllars.py --config .\playground.example.json --prompt "mcp capability smoke"`
	- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"`
	- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`
