# T60 Fix Docker Runtime project_root Guard Failure

## Metadata
- Status: Done
- Priority: P1
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Docker runtime startup fails because runtime config sets `run.project_root` to an
absolute path (`/work`), but runtime guard rejects absolute project_root values.

## Objective
Make Docker runtime config compatible with project_root guard behavior.

## Scope
- Remove incompatible `run.project_root` override from Docker runtime config.
- Keep mount roots unchanged.
- Update docs to reflect effective project_root behavior in serve mode.

## Non-Goals
- No runtime guard policy changes.
- No compose topology changes.

## Target Files
- docker/runtime.container.json
- docs/docker_runtime.md

## Verification
- PASS: docker compose -f .\\docker-compose.runtime.yml config
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"

## Rollback
Restore removed `run.project_root` field in runtime container config.

## Completion Artifact
Runtime container config without absolute project_root and passing validation commands.

## Completion Notes
- Removed `run.project_root` from Docker runtime config to avoid absolute-path
	rejection by `resolve_project_root`.
- Preserve effective project root as `/work` via `service.mount_work_root` when
	`run.project_root` is unset in serve mode.
