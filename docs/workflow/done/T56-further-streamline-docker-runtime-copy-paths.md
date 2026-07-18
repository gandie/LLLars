# T56 Further Streamline Docker Runtime Copy Paths

## Metadata
- Status: Done
- Priority: P2
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
The first streamlining pass still left duplicate seed copies in image build steps.
The same source files were staged under defaults directories even though they can
be copied directly from canonical image paths during startup.

## Objective
Reduce Docker runtime copy steps further while preserving first-run behavior and
command profile availability.

## Scope
- Remove redundant default copy staging in Docker image build.
- Update runtime entrypoint to copy missing files from canonical source paths.
- Keep command profile file present under `/work` when missing.
- Update Docker runtime docs for revised seeding behavior.

## Non-Goals
- No compose changes.
- No runtime API behavior changes.

## Target Files
- Dockerfile.runtime
- docker/runtime-entrypoint.sh
- docs/docker_runtime.md

## Verification
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- PASS: docker compose -f .\\docker-compose.runtime.yml config

## Rollback
Restore previous defaults staging copies in Dockerfile and entrypoint.

## Completion Artifact
Focused diff with redundant copy staging removed and validations passing.

## Completion Notes
- Removed redundant staging copies for `.env.runtime.example`,
	`runtime.container.json`, and `playground.command-profiles.yaml` from image build.
- Retained only playground content seeding into `/opt/lllars/defaults/work`.
- Updated startup logic to backfill missing runtime files from canonical image
	source paths under `/opt/lllars`.
- Preserved command profile availability in `/work` through missing-file copy.
