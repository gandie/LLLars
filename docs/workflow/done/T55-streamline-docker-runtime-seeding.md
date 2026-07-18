# T55 Streamline Docker Runtime Seeding

## Metadata
- Status: Done
- Priority: P2
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
The Docker runtime setup currently seeds defaults through multiple copy paths that
partially overlap. This makes startup behavior harder to reason about and misses
an explicit runtime path for external command profile configuration.

## Objective
Reduce duplicate copy behavior in Docker runtime setup and ensure command profile
configuration is present in container runtime defaults.

## Scope
- Simplify default-seeding layout in Docker build and entrypoint.
- Ensure default runtime config references an external command profile source.
- Ensure command profile source file is present in seeded `/work` defaults.
- Update Docker runtime operator docs to reflect resulting behavior.

## Non-Goals
- No runtime API behavior changes.
- No queue backend changes.
- No command profile policy redesign.

## Target Files
- Dockerfile.runtime
- docker/runtime-entrypoint.sh
- docker/runtime.container.json
- docs/docker_runtime.md

## Verification
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- PASS: docker compose -f .\\docker-compose.runtime.yml config

## Rollback
Restore prior Dockerfile/entrypoint copy logic and runtime container defaults.

## Completion Artifact
Focused diff plus passing markdown boundary test and compose config rendering.

## Completion Notes
- Consolidated seeded runtime defaults so `runtime.container.json` and
	`playground.command-profiles.yaml` are both sourced from `/opt/lllars/defaults/work`.
- Removed duplicate runtime-config fallback source from `defaults/config`.
- Added default `run` fields in Docker runtime config to point at external command
	profile config in `/work`.
- Updated Docker runtime documentation with seeded `/work` contents and command
	profile defaults.
