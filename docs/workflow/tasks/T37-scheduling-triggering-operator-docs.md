# T37 Scheduling and Triggering Operator Docs

## Metadata
- Status: Proposed
- Priority: P2
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

## Objective
Document timed, scheduled, recurring, and trigger flows for operators.

## Scope
- End-to-end usage examples for new run modes.
- Failure-mode and recovery guidance.
- Smoke test scenarios aligned to docs.

## Non-Goals
- No frontend scheduler UX.
- No benchmark claims.

## Target Files
- README.md
- docs/DESIGN.md
- runtime_api_smoke_test.py
- tests/test_runtime_api_smoke_test.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_test.py"
- .\\venv\\Scripts\\python.exe .\\runtime_api_smoke_test.py --prompt "scheduling docs smoke"

## Rollback
Keep existing submit/status docs as baseline sections.

## Completion Artifact
Operator docs plus passing smoke checks.
