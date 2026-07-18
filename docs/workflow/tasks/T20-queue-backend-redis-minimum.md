# T20 Queue Backend: Redis Minimum

## Metadata
- Status: Deferred
- Priority: P2
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

## Objective
Implement a redis queue backend baseline for submit/status/cancel lifecycle.

## Scope
- Redis-backed job state persistence with existing transition rules.
- Serve-mode dispatch path for `queue_backend=redis`.
- Startup diagnostics for unreachable or misconfigured redis.

## Non-Goals
- No distributed scheduling layer.
- No dead-letter or retry policy framework.

## Target Files
- lllars_core/job_store.py
- lllars_core/runtime/service.py
- pyproject.toml
- tests/test_runtime_api.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api.py"
- .\\venv\\Scripts\\python.exe .\\lllars.py serve --config .\\playground.example.json --queue-backend redis

## Rollback
Keep in-memory backend as default and gate redis path behind explicit selection.

## Completion Artifact
Diff and tests showing both in-memory and redis backend selection behavior.
