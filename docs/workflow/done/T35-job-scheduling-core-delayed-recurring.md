# T35 Job Scheduling Core (Delayed and Recurring)

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-19

## Why Needed
`JobSpec` already exposed `run_at` and `schedule` contract fields, but runtime execution still behaved as immediate-submit only. T35 is needed to operationalize delayed and recurring execution in core runtime behavior while preserving submit-now compatibility.

## Objective
Add delayed (`run_at`) and recurring schedule support inside the runtime package.

## Scope
- Schedule metadata and next-run persistence.
- Scheduler loop promoting due jobs.
- Minimal recurrence parser and validator.
- Minimal frontend adjustment to submit, run and view timed jobs

## Non-Goals
- No distributed scheduler clustering.
- No UI calendar workflow. Use native html date input

## Target Files
- lllars_core/runtime/scheduler.py
- lllars_core/runtime/service.py
- lllars_core/runtime/models.py
- lllars_core/job_store.py
- lllars_core/job_store_record.py
- lllars_core/runtime/__init__.py
- lllars_core/static/runtime/index.html
- tests/test_job_store.py
- tests/runtime_api_test_support.py
- tests/test_runtime_api_submission.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_job_store.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_submission.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- .\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\

## Rollback
Keep scheduler opt-in and preserve immediate submit as default.

## Completion Artifact
Scheduled and recurring execution tests passing.

## Completion Notes
- Added runtime scheduler loop in `lllars_core/runtime/scheduler.py` with due-job promotion and interval parser/validator for grammar `every:<int><unit>` (`s|m|h|d`).
- Integrated scheduler into `RuntimeService` so immediate jobs still start at submit, delayed `run_at` jobs are promoted when due, and recurring scheduled jobs are re-queued with `next_run_at` after each run.
- Extended job persistence with schedule metadata (`next_run_at`, `last_run_at`, `run_count`) and recurring lifecycle helpers (`mark_running`, `reschedule_recurring`).
- Extended API status model to expose scheduling metadata and enforced schedule grammar validation in `JobSpec`.
- Added minimal runtime frontend fields for `run_at` and `schedule`, and status note display for upcoming run timing.
- Resolved runtime/job_store import cycle structurally by removing `runtime.models` import-time dependencies from job store modules (`job_store.py`, `job_store_record.py`) and restoring explicit eager exports in `lllars_core/runtime/__init__.py`.

## Validation Results
- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_job_store.py"`
- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_submission.py"`
- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"`
- PASS `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
