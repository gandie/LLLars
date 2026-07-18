# T58 Split Dockerfile Runtime RUN Steps

## Metadata
- Status: Done
- Priority: P1
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Operator requested explicit separate RUN instructions instead of a chained
single RUN block in Dockerfile runtime build steps.

## Objective
Replace chained runtime build RUN block with separate RUN steps.

## Scope
- Split Dockerfile.runtime build commands into separate RUN instructions.
- Preserve existing build behavior and entrypoint wiring.

## Non-Goals
- No compose changes.
- No runtime behavior redesign.

## Target Files
- Dockerfile.runtime

## Verification
- PASS: docker compose -f .\\docker-compose.runtime.yml config
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"

## Rollback
Restore previous single RUN block in Dockerfile.runtime.

## Completion Artifact
Dockerfile with separate RUN instructions and passing compose config render.

## Completion Notes
- Replaced single chained RUN block with explicit separate RUN instructions.
- Preserved operation order and behavior for apt, shell check, install, and entrypoint chmod.
