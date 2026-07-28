---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-07-28
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
    validation_trust: 5

  collaboration:
    ambiguity_handling: 5
    operator_load: 5
    trust_delta: 5

  notes: >
    Flawless.
---

# T79 Runtime Frontend Feature Parity

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-28

## Why Needed
The runtime UI does not fully expose all available runtime configuration fields, which creates operator blind spots and API/UI drift.

## Objective
Update the runtime frontend to support all currently available runtime features and configuration knobs exposed by the payload contract.

## Scope
- Audit current JobSpec/run payload fields versus UI controls.
- Add missing UI controls for supported fields.
- Ensure payload serialization and null/optional handling align with API models.
- Add/extend tests for UI payload shaping and runtime submission behavior.

## Non-Goals
- No backend contract expansion in this task.
- No styling-overhaul effort beyond required usability updates.
- Change of current field default values! These are adjusted by humans!

## Target Files
- lllars_core/static/runtime/index.html
- lllars_core/runtime/models.py
- tests/test_runtime_api_submission.py
- tests/test_runtime_api_surface.py
- docs/runtime_api.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert UI control additions and restore prior payload-shaping behavior.

## Completion Artifact
UI exposes all supported runtime controls with passing submission/surface tests.

## Completion Notes
- Added missing runtime frontend controls for submit payload parity across `JobSpec` and `JobSpec.run` fields: `config_path`, `deadline_at`, `trigger_source`, `trigger_payload_ref`, `shell_mode`, `shell_override`, `enabled_tool_groups`, and `plugin_tool_paths`.
- Aligned frontend payload serialization for optional/null values and compatibility command fields by emitting `test_command` and `eval_command` alongside `commands.test`/`commands.eval`.
- Extended runtime API tests to validate submit acceptance and frontend surface exposure of new payload controls/keys.
- Updated runtime API docs with the expanded frontend parity surface and payload notes.
- Validation results:
  - PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api_submission.py"`
  - PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api_surface.py"`
  - PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
  - PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`