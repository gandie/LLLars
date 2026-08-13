---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-08-13
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
    scope_discipline: 3
    validation_trust: 3

  collaboration:
    ambiguity_handling: 1
    operator_load: 2
    trust_delta: 3

  notes: >
    Again much friction with boundaries and other stuff. Clumsy and sloppy.
---

# T86 Fix Runtime External Profile Override Resolution

## Metadata
- Owner: unassigned
- Created: 2026-08-13
- Updated: 2026-08-13

## Why Needed
Runtime job-level command_profile overrides fail for external profiles that exist in the configured profile map but are not the startup-selected default profile.

## Objective
Ensure runtime command_profile override validation and command resolution use the full externally loaded profile map, not only built-ins plus selected default profile.

## Scope
- Persist resolved command-profile registry in loaded harness config state.
- Update runtime override validation and command lookup to use persisted registry.
- Add regression coverage for overriding from one external profile to another.

## Non-Goals
- No changes to wildcard semantics or yolo tool-group behavior.
- No changes to command profile file format.

## Target Files
- lllars_core/config/models.py
- lllars_core/config/loader_steps.py
- lllars_core/config/runtime_inputs_builder.py
- lllars_core/config/harness_builder.py
- lllars_core/config/loader.py
- lllars_core/runtime/settings.py
- tests/test_runtime_runner_overrides.py

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert runtime profile-registry persistence and restore previous runtime settings resolution path.

## Completion Artifact
Runtime can override to any valid external command profile from configured profile maps, covered by regression tests and recorded in changelog.

## Validation Evidence
- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"`
- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_runner_overrides.py"`
- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"`
- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`
