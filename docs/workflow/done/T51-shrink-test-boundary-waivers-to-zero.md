# T51 Shrink Test Boundary Waivers to Zero

## Metadata
- Status: Completed
- Priority: P1
- Owner: Copilot
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Test files are now in refactor-boundary scope, but several test modules still rely on file/function waivers. This weakens governance and obscures maintainability debt.

## Objective
Refactor oversized test modules/functions using reusable helpers so tests pass default refactor boundaries with zero test waivers.

## Scope
- Remove test-file waivers from docs/refactor_boundaries.json.
- Introduce reusable test helpers for repeated setup/assertion patterns.
- Split and simplify oversized test modules/functions to stay within defaults.

## Non-Goals
- No runtime production behavior changes.
- No boundary limit changes.

## Target Files
- docs/refactor_boundaries.json
- tests/*.py (targeted refactors)
- tests/helpers/*.py (new reusable helpers as needed)

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"

## Rollback
Restore removed waivers and revert helper extraction if behavior regresses.

## Completion Notes
- Removed all test waivers from `docs/refactor_boundaries.json`.
- Split oversized test modules into focused files:
	- CLI: `tests/test_cli_shell_detection.py`, `tests/test_cli_commands.py`
	- Config: `tests/test_config_service_modes.py`, `tests/test_config_runtime_paths.py`
	- Runtime API: `tests/test_runtime_api_surface.py`, `tests/test_runtime_api_submission.py`, `tests/test_runtime_api_failures.py`, `tests/test_runtime_service_artifacts.py`
	- Runtime runner: `tests/test_runtime_runner_exports.py`, `tests/test_runtime_runner_flow.py`, `tests/test_runtime_runner_overrides.py`
- Added shared helper modules:
	- `tests/cli_test_support.py`
	- `tests/config_test_support.py`
	- `tests/runtime_api_test_support.py`
	- `tests/runtime_runner_test_support.py`
- Reduced remaining oversized test functions in `tests/test_runtime_api_smoke_test.py` and `tests/test_job_store.py` via helper extraction.
- Removed superseded oversized modules:
	- `tests/test_cli_regression.py`
	- `tests/test_config.py`
	- `tests/test_runtime_api.py`
	- `tests/test_runtime_runner.py`

## Validation Evidence
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" -> OK (1 test)
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -> OK (54 tests)
