# T36 Job Triggering Integration

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-20

## Why Needed
Scheduled jobs existed, but operators had no explicit runtime route to trigger queued jobs on demand and no stable metadata trail from trigger event to run/artifacts.

## Objective
Introduce explicit trigger pathways for API and internal scheduler events.

## Scope
- Trigger metadata (`trigger_source`, `trigger_payload_ref`) across run lifecycle.
- Trigger route contract for queued jobs with default metadata.
- Artifact linkage from trigger event to spawned run.
- Minimal frontend to visualize queue and offer manual trigger

## Non-Goals
- No external event bus integration.
- No auth redesign.

## Target Files
- lllars_core/runtime/service.py
- lllars_core/runtime/service_triggering.py
- lllars_core/runtime/models.py
- lllars_core/runtime/api.py
- lllars_core/runtime/artifacts.py
- lllars_core/job_store.py
- lllars_core/job_store_record.py
- lllars_core/static/runtime/index.html
- tests/test_runtime_api_surface.py
- tests/test_runtime_api_submission.py
- tests/test_runtime_api_triggering.py
- tests/test_runtime_api_failures.py
- tests/test_job_store.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_submission.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_triggering.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_surface.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_failures.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_job_store.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- .\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\

## Rollback
Keep direct submit contract as fallback pathway.

## Completion Artifact
Trigger-flow API tests with auditable metadata.

## Completion Notes
- Added `POST /jobs/{job_id}/trigger` for queued jobs and `GET /jobs` for queue visibility.
- Trigger request defaults are now explicit and minimal: `trigger_source="manual"`, `trigger_payload_ref=null`.
- Persisted trigger metadata across lifecycle in status payloads and artifact summary linkage.
- Runtime UI now renders queued jobs and supports one-click manual trigger.
- Validation results:
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_submission.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_triggering.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_surface.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_failures.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_job_store.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"`
	- PASS `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
