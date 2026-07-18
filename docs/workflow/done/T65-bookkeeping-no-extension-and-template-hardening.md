# T65 Bookkeeping No-Extension and Template Hardening

## Metadata
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Bookkeeping conventions drifted with ad-hoc task metadata fields that are not
required by folder-based state management. This creates hidden protocol
extensions and operator-control friction.

## Objective
Make bookkeeping protocol non-extendable and add a mandatory task template that
omits status and priority fields.

## Scope
- Add explicit no-extension rule to bookkeeping skill.
- Add mandatory task template section in bookkeeping skill.
- Mirror mandatory template and no-extension contract in workflow README.

## Non-Goals
- No runtime code changes.
- No historical task file rewrites.

## Target Files
- .github/skills/bookkeeping/SKILL.md
- docs/workflow/README.md

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"

## Rollback
Restore prior bookkeeping skill and workflow README wording.

## Completion Artifact
Bookkeeping docs enforce non-extendable protocol and mandatory task template without status/priority metadata fields.

## Completion Notes
- Added explicit no-extension rule in bookkeeping skill: folder location is the
	only lifecycle status protocol.
- Added explicit ban on lifecycle metadata extensions (`Status`, `Priority`,
	and similar custom fields) in task files.
- Added mandatory task template in bookkeeping skill and workflow README that
	omits lifecycle status/priority fields.
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
