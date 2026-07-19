# T34 Timed Job Runs (Runtime Deadlines)

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-19

## Why Needed
Runtime jobs currently honor only static `timeout_sec`, while scheduling contracts already expose `deadline_at` without execution enforcement. T34 is needed to ensure deadline-bearing jobs terminate deterministically through the runtime timeout path and expose deadline termination evidence in telemetry.

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
- lllars_core/runtime/job_runner.py
- lllars_core/runtime/job_runner_flow.py
- lllars_core/runtime/results.py
- lllars_core/runtime/final_result.py
- tests/runtime_runner_test_support.py
- tests/test_runtime_runner_flow.py
- tests/test_runtime_runner_deadlines.py
- tests/test_runtime_api_submission.py
- tests/test_runtime_api_failures.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_runner_flow.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_runner_deadlines.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_submission.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_failures.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\

## Rollback
Gate deadline enforcement behind config fallback.

## Completion Artifact
Deterministic timeout-state tests passing.

## Completion Notes
- Enforced per-job execution deadlines by resolving effective runtime timeout from `timeout_sec` and optional `deadline_at`, including immediate timeout when deadline is already expired.
- Added timeout terminal-state short-circuit so timeout outcomes skip post-agent tests/eval and produce deterministic `eval_error="timeout"` terminal results.
- Added runtime telemetry deadline markers (`deadline_limited`, `expired_before_start`, `reached`, `termination`) for deadline-reached termination visibility.
- Added timezone-naive datetime validation for `deadline_at` and `run_at` to keep deterministic runtime comparisons.
- Follow-up cleanup: removed timezone-aware runtime branching in deadline timeout resolution and standardized on naive `datetime.now()`.
- Follow-up docs update: documented naive ISO datetime contract (`YYYY-MM-DDTHH:MM:SS`) and explicit rejection of offset-bearing values.
- Follow-up workflow cleanup: removed duplicate active task copy and kept this `done/` artifact as canonical T34 record.
- Validation results:
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_runner_flow.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_runner_deadlines.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_submission.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_failures.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
