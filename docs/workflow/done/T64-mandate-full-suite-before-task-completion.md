# T64 Mandate Full Suite Before Task Completion

## Metadata
- Status: Done
- Priority: P1
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Recent regressions were only caught when the full test suite was run after task
completion bookkeeping had already started. Completion rules must explicitly
require full-suite validation before moving tasks to done.

## Objective
Make full-suite test execution mandatory before task completion.

## Scope
- Update bookkeeping skill completion protocol.
- Update workflow README operating rules for completion gating.
- Use explicit command: `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`.

## Non-Goals
- No runtime code changes.
- No test logic changes.

## Target Files
- .github/skills/bookkeeping/SKILL.md
- docs/workflow/README.md

## Verification
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"

## Rollback
Restore prior bookkeeping/workflow wording if the requirement must be relaxed.

## Completion Artifact
Bookkeeping and workflow docs requiring full-suite unittest discover pass before moving tasks to done.

## Completion Notes
- Added hard-rule completion gate in bookkeeping skill requiring full-suite pass
	via `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`.
- Added explicit completion protocol step to run full suite before changelog and
	moving tasks to `done/`.
- Mirrored the same mandatory sequence in workflow README operating rules.
