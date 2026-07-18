# T35 Job Scheduling Core (Delayed and Recurring)

## Metadata
- Status: Proposed
- Priority: P1
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

## Objective
Add delayed (`run_at`) and recurring schedule support inside the runtime package.

## Scope
- Schedule metadata and next-run persistence.
- Scheduler loop promoting due jobs.
- Minimal recurrence parser and validator.

## Non-Goals
- No distributed scheduler clustering.
- No UI calendar workflow.

## Target Files
- lllars_core/runtime/scheduler.py
- lllars_core/runtime/service.py
- lllars_core/runtime/models.py
- lllars_core/job_store.py
- tests/test_job_store.py
- tests/test_runtime_api.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_job_store.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"

## Rollback
Keep scheduler opt-in and preserve immediate submit as default.

## Completion Artifact
Scheduled and recurring execution tests passing.
