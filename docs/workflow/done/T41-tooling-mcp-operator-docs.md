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
    correctness: 5
    scope_discipline: 5
    validation_trust: 4

  collaboration:
    ambiguity_handling: 5
    operator_load: 4
    trust_delta: 4

  notes: >
    Last task to fix yaml frontmatter before test catches the idiot.
    Implementation seems sound though.
---

# T41 Tooling and MCP Operator Docs

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-27

## Why Needed
Tool registry and MCP capability behavior changed from fixed wiring to
configurable/graded behavior, but operator-facing documentation does not yet
show copy-paste setup, migration guidance, or recovery playbooks for degraded
and unavailable MCP states.

## Objective
Document configuration, troubleshooting, and migration for tool extensibility and MCP changes.

## Scope
- Native/plugin tool configuration how-to.
- MCP health/degraded/unavailable troubleshooting matrix.
- Migration guide from fixed wiring to configurable registry.

## Non-Goals
- No UI documentation portal.
- No full plugin SDK tutorial.

## Target Files
- README.md
- docs/DESIGN.md
- playground.example.json

## Verification
- Manual docs walkthrough using example configs.

## Rollback
Keep old docs sections available until next release cycle.

## Completion Artifact
Operator docs with copy-paste examples and recovery playbooks.

## Completion Notes
- Added a README operator guide for configurable tool groups, local plugin
	path configuration, MCP capability troubleshooting, and migration from fixed
	wiring.
- Updated DESIGN section from draft wording to shipped runtime semantics,
	including capability-aware fallback behavior and current MCP gating notes.
- Expanded `playground.example.json` with explicit `run.tool_groups` and
	`run.tool_plugins.paths` examples.
- Manual walkthrough completed against the updated README examples and
	playground config fields.
- Validation results:
	- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
	- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`