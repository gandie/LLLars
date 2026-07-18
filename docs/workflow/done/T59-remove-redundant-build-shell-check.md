# T59 Remove Redundant Build Shell Check

## Metadata
- Status: Done
- Priority: P1
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Dockerfile runtime build still includes a shell-detection RUN command that is
redundant with runtime shell detection in the entrypoint.

## Objective
Remove redundant build-time shell check and keep runtime shell detection as the
single source of truth.

## Scope
- Remove shell-check RUN line from Dockerfile.runtime.
- Keep entrypoint runtime shell detection unchanged.

## Non-Goals
- No runtime behavior changes beyond removing redundant build step.

## Target Files
- Dockerfile.runtime

## Verification
- PASS: docker compose -f .\\docker-compose.runtime.yml config
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"

## Rollback
Restore the removed shell-check RUN command.

## Completion Artifact
Dockerfile without redundant shell-check RUN instruction and passing compose config rendering.

## Completion Notes
- Removed build-time shell detection RUN instruction from Dockerfile.
- Kept runtime shell detection in entrypoint as the single authoritative check.
