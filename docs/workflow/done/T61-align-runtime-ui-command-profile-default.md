# T61 Align Runtime UI Command Profile Default

## Metadata
- Status: Done
- Priority: P1
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Runtime UI advanced settings still default `command_profile` to
`python-playground`, while Docker runtime defaults now use
`playground-python` with Docker-scoped command profile config.

## Objective
Align runtime UI default command profile with current Docker runtime defaults.

## Scope
- Update runtime frontend default command profile value.

## Non-Goals
- No API contract changes.
- No runtime profile resolution logic changes.

## Target Files
- lllars_core/static/runtime/index.html

## Verification
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"

## Rollback
Restore UI default command profile value to `python-playground`.

## Completion Artifact
Runtime UI defaults aligned with Docker runtime profile naming.

## Completion Notes
- Updated runtime UI advanced settings default `command_profile` from
	`python-playground` to `playground-python` to match Docker runtime defaults.
