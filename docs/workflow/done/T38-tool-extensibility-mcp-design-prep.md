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
    correctness: 4
    scope_discipline: 4
    validation_trust: 4

  collaboration:
    ambiguity_handling: 5
    operator_load: 4
    trust_delta: 3

  notes: >
    Seems OK, might contain traps later down the line though.
    Agent still fucks up YAML like a moron
---

# T38 Tool Extensibility and MCP Design Prep

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-27

## Why Needed
Current tool registration is fixed to native file/shell wiring and MCP enablement at load time, which leaves no explicit contract for group-level configuration, local plugin onboarding, or capability-aware MCP fallback. T39 and T40 need a shared design baseline to avoid incompatible semantics.

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
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Keep fixed wiring and treat design as draft until T39 and T40 land.

## Completion Artifact
Approved design checklist for T39 and T40.

## Completion Notes
- Added `docs/DESIGN.md` section defining tool taxonomy, registration boundaries, config schema draft, capability matrix states, and degraded-continue fallback policy.
- Added draft seam constants in `lllars_core/tools/registry.py` for stable tool-group names planned for T39.
- Added draft capability classification helpers in `lllars_core/mcp/runtime.py` for T40 planning without changing runtime behavior.
- Locked ambiguity decisions for follow-up implementation:
	- `tool_groups.enabled` and `tool_groups.disabled` overlap is a config error.
	- MCP partial availability uses degraded-continue fallback.
- Validation results:
	- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
	- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`
