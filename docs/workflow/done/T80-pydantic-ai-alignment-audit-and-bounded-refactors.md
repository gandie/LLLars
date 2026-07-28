---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: YYYY-MM-DD
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
    ambiguity_handling: 4
    operator_load: 4
    trust_delta: 3

  notes: >
    Would have expected more findings, simplification and docs research.
---

# T80 Pydantic AI Alignment Audit And Bounded Refactors

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-28

## Why Needed
Custom wrappers remain around framework-native capabilities; a bounded audit is needed to reduce maintenance drift and avoid unnecessary bespoke behavior.

## Objective
Run a docs-first pydantic_ai alignment audit, then implement only the highest-value 1-2 bounded refactors that remove or simplify custom framework-native replacements.

## Scope
- Produce an audit matrix of current custom implementations versus pydantic_ai native features.
- Identify and prioritize bounded refactor slices with risk notes.
- Implement only approved bounded slices with tests.
- Update docs to reflect post-refactor native usage.

## Non-Goals
- No broad rewrite of agent/runtime architecture.
- No unbounded refactor campaign in a single task.

## Target Files
- lllars_core/agent_builder.py
- lllars_core/runtime/
- lllars_core/tools/
- docs/DESIGN.md
- docs/configuration.md
- tests/

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert bounded refactor commits and retain prior wrapper behavior.

## Completion Artifact
Audit report exists, selected bounded slices are implemented, and full-suite regressions are clear.

## Audit Matrix (Docs-First)
Source docs consulted:
- https://pydantic.dev/docs/ai/overview/
- https://pydantic.dev/docs/ai/core-concepts/agent/
- https://pydantic.dev/docs/ai/tools-toolsets/tools/

| Area | Current Custom Implementation | Native pydantic_ai Capability | Gap / Drift Risk | Priority |
| --- | --- | --- | --- | --- |
| Shell tool retry signaling | `run_allowlisted_shell` raises `ModelRetry` but immediately catches `Exception` and converts to string error payload | `ModelRetry` should propagate to agent retry loop for model self-correction | Native retry path was suppressed by broad exception handling | P0 |
| Shell test/eval tool retry propagation | `run_test_command` / `run_eval_command` catch all exceptions | `ModelRetry` should be allowed to propagate when surfaced from lower layers | Future recoverable retries could be silently downgraded to terminal errors | P1 |
| Agent builder wrapper helpers | `_register_file_tools` / `_register_shell_tools` wrappers existed but were unused | Direct registration path already present via `register_runtime_tools` | Unused indirection increases maintenance drift and confusion | P2 |
| Usage limits / retries wiring | Config maps into `UsageLimits` and `retries` on `Agent` | Native support exists and is already used | No blocking drift; retain current shape | P3 |

## Selected Bounded Slices
1. Preserve native `ModelRetry` propagation in shell tools (P0/P1).
2. Remove dead wrapper helpers in agent builder (P2).

Risk notes:
- Slice 1 changes error control flow for recoverable failures only; non-recoverable paths still return tool-error payloads.
- Slice 2 is no-behavior cleanup; wrappers were not referenced by runtime call paths.

## Implementation Notes
- Updated `lllars_core/tools/shell_policy.py` to re-raise `ModelRetry` in:
	- `run_allowlisted_shell`
	- `run_test_command`
	- `run_eval_command`
- Removed unused helper wrappers from `lllars_core/agent_builder.py`:
	- `_register_file_tools`
	- `_register_shell_tools`
- Added regression tests in `tests/test_agent_builder.py` to verify:
	- invalid allowlisted shell command ID raises `ModelRetry`
	- test command tool propagates `ModelRetry`

## Validation Evidence
- PASS `./venv/Scripts/python.exe -m unittest discover -s tests -p "test_agent_builder.py"`
- PASS `./venv/Scripts/python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
- PASS full suite `./venv/Scripts/python.exe -m unittest discover ./tests/`