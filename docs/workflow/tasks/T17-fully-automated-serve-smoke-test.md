# T17 Fully Automated Serve Smoke Test

## Metadata
- Status: Ready
- Priority: P0
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

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
- runtime_api_smoke_test.py
- tests/test_cli_regression.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_test.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_cli_regression.py"

## Rollback
Keep current contract-style smoke tests while adding isolated automated harness tests.

## Completion Artifact
CI-friendly unittest output proving serve smoke is fully automated.
