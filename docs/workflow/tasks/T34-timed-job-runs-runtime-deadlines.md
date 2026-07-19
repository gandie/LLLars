# T34 Timed Job Runs (Runtime Deadlines)

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

## Objective
Add per-job execution deadlines so long-running jobs stop deterministically.

## Scope
- Optional per-job deadline fields with validation.
- Deadline enforcement path to terminal timeout outcome.
- Runtime telemetry markers for deadline-reached termination.

## Non-Goals
- No recurring scheduling.
- No queue backend redesign.

## Target Files
- lllars_core/runtime/models.py
- lllars_core/runtime/execution.py
- lllars_core/runtime/service.py
- tests/test_runtime_runner.py
- tests/test_runtime_api.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_runner.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"

## Rollback
Gate deadline enforcement behind config fallback.

## Completion Artifact
Deterministic timeout-state tests passing.
