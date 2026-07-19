# T36 Job Triggering Integration

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

## Objective
Introduce explicit trigger pathways for API and internal scheduler events.

## Scope
- Trigger metadata (`trigger_source`, `trigger_payload_ref`) across run lifecycle.
- Trigger route/action contract for preconfigured jobs.
- Artifact linkage from trigger event to spawned run.

## Non-Goals
- No external event bus integration.
- No auth redesign.

## Target Files
- lllars_core/runtime/web.py
- lllars_core/runtime/service.py
- lllars_core/runtime/models.py
- lllars_core/runtime/execution.py
- tests/test_runtime_api.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"

## Rollback
Keep direct submit contract as fallback pathway.

## Completion Artifact
Trigger-flow API tests with auditable metadata.
