# T17 Fully Automated Serve Smoke Test

## Metadata
- Status: Done
- Priority: P0
- Owner: Copilot
- Created: 2026-07-16
- Updated: 2026-07-18

## Why Needed
Serve smoke verification depended on a manual two-terminal sequence,
which made regressions hard to catch in CI and non-deterministic during
local validation.

## Objective
Remove manual two-terminal operator flow from serve smoke verification.

## Scope
- Add in-process serve harness on ephemeral port.
- Add deterministic timeout and teardown behavior.
- Cover terminal states `succeeded`, `failed`, and `canceled`.

## Non-Goals
- No docker compose dependency in unit tests.
- No performance benchmark coverage.

## Target Files
- tests/test_runtime_api_smoke_test.py
- tests/runtime_api_smoke_harness.py
- runtime_api_smoke_test.py
- tests/test_cli_regression.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_test.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_cli_regression.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- .\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\

## Rollback
Keep current contract-style smoke tests while adding isolated automated harness tests.

## Completion Artifact
CI-friendly unittest output proving serve smoke is fully automated.

## Completion Notes
- Added an in-process HTTP serve harness bound to an ephemeral local port
	for smoke API verification without manual terminal orchestration.
- Extracted harness internals into `tests/runtime_api_smoke_harness.py`
	to restore refactor-boundary compliance for test-file size limits.
- Added deterministic timeout-path testing by injecting monotonic/sleep
	callables into `run_smoke_test`.
- Added terminal-state coverage for `succeeded`, `failed`, and `canceled`
	against live HTTP requests.
- Added smoke CLI regression coverage for shell-list normalization and
	empty-shell argument rejection.

## Validation Evidence
- PASS: `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_test.py"`
- PASS: `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_cli_regression.py"`
- PASS: `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"`
- PASS: `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
