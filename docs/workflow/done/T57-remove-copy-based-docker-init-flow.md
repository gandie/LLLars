# T57 Remove Copy-Based Docker Init Flow

## Metadata
- Status: Done
- Priority: P1
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
The Docker runtime startup still performed file copy-based initialization into
mounted volumes, which adds noisy volume state and obscures the source of truth
for runtime configuration.

## Objective
Remove copy-based initialization and use direct canonical runtime config/profile
paths from the image.

## Scope
- Remove defaults staging/copy chain from Docker build.
- Remove startup file copy logic from entrypoint.
- Run serve with direct config path in image.
- Provide Docker-specific command profile file in image and reference it by
  absolute path in runtime config.
- Update docker runtime docs to match direct-path behavior.

## Non-Goals
- No runtime API contract changes.
- No compose service topology changes.

## Target Files
- Dockerfile.runtime
- docker/runtime-entrypoint.sh
- docker/runtime.container.json
- docker/runtime.command-profiles.yaml
- docs/docker_runtime.md

## Verification
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- PASS: docker compose -f .\\docker-compose.runtime.yml config

## Rollback
Restore copy-based defaults staging and entrypoint fallback copy logic.

## Completion Artifact
Focused diff showing zero startup copy operations for runtime config/profile/env defaults.

## Completion Notes
- Removed copy-staging from Docker build; image no longer prepares defaults trees
  for runtime config/profile/env files.
- Removed startup copy logic from entrypoint and switched to direct config path:
  `--config /opt/lllars/docker/runtime.container.json`.
- Added Docker-scoped command profile file at
  `/opt/lllars/docker/runtime.command-profiles.yaml` and wired runtime config to
  it via absolute path.
- Kept `/work`, `/config`, `/artifacts` directory creation only.
- Replaced Dockerfile `&&` command chaining with a fail-fast `set -eu` shell
  block and command separators for clearer operational flow.
