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
    validation_trust: 5

  collaboration:
    ambiguity_handling: 5
    operator_load: 5
    trust_delta: 5

  notes: >
    Flawless execution with disciplined scope and explicit validation evidence.
---

# T37 Scheduling and Triggering Operator Docs

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-27

## Why Needed
Operators have scheduling and trigger runtime capabilities in code, but the top-level docs and smoke guidance do not yet provide a single operational path for timed, recurring, and manual trigger execution and recovery.

## Objective
Document timed, scheduled, recurring, and trigger flows for operators.

## Scope
- End-to-end usage examples for new run modes.
- Failure-mode and recovery guidance.
- Smoke test scenarios aligned to docs.

## Non-Goals
- No full fleshed frontend scheduler UX.
- No benchmark claims.

## Target Files
- README.md
- docs/DESIGN.md
- runtime_api_smoke_test.py
- tests/test_runtime_api_smoke_test.py
- tests/test_runtime_api_smoke_modes.py

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_test.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_modes.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover .\tests\
- .\venv\Scripts\python.exe .\runtime_api_smoke_test.py --prompt "scheduling docs smoke"

## Rollback
Keep existing submit/status docs as baseline sections.

## Completion Artifact
Operator docs plus passing smoke checks.

## Completion Notes
- Added operator-facing scheduling and triggering flow guidance in README and DESIGN, including end-to-end run modes and recovery paths tied to current runtime behavior.
- Extended runtime_api_smoke_test.py with mode-driven scenarios: immediate, timed, recurring, and trigger.
- Added focused mode coverage in tests/test_runtime_api_smoke_modes.py while preserving baseline script checks in tests/test_runtime_api_smoke_test.py.
- Validation results:
  - PASS .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_test.py"
  - PASS .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_modes.py"
  - PASS .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
  - PASS .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
  - PASS .\venv\Scripts\python.exe -m unittest discover .\tests\
  - FAIL .\venv\Scripts\python.exe .\runtime_api_smoke_test.py --prompt "scheduling docs smoke" (no runtime server listening on http://127.0.0.1:8000 during this run; command requires active runtime service precondition)
