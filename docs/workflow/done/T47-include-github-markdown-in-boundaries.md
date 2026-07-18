# T47 Include .github Markdown in Boundaries

## Metadata
- Status: Done
- Priority: P1
- Owner: Friday
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Agent and skill definitions in .github are operational guardrails. They need the same size discipline as repository docs so instruction surfaces remain concise and maintainable.

## Objective
Extend markdown boundary checks to include .github markdown files.

## Scope
- Add .github markdown glob patterns to boundary include configuration.
- Validate boundary and full test baseline.

## Non-Goals
- No changes to runtime code.
- No changes to existing waiver policy values.

## Target Files
- docs/markdown_boundaries.json

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py" -> PASS
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_*.py" -> PASS

## Rollback
Remove .github include globs from docs/markdown_boundaries.json if policy scope must be narrowed.

## Completion Notes
- Boundary coverage now includes .github agent and skill markdown files.
- Existing .github markdown files passed current boundary limits without additional waivers.