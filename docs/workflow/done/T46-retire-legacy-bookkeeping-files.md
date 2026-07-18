# T46 Retire Legacy Bookkeeping Files

## Metadata
- Status: Done
- Priority: P1
- Owner: Friday
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
The repository now uses the workflow skill and folder-driven bookkeeping model as the active contract. Keeping seed and legacy implementation files creates duplicate sources of truth and stale references.

## Objective
Delete superseded bookkeeping and implementation files.

## Scope
- Remove `docs/BOOKKEEPING_WORKFLOW_PLAN.md`.
- Remove `docs/IMPLEMENTATION_PREP.md`.
- Remove `docs/IMPLEMENTATION_CHANGELOG.md`.
- Update remaining live references to point to the active workflow model.

## Non-Goals
- No runtime behavior changes.
- No Python module or API changes.

## Target Files
- docs/BOOKKEEPING_WORKFLOW_PLAN.md
- docs/IMPLEMENTATION_PREP.md
- docs/IMPLEMENTATION_CHANGELOG.md
- docs/DESIGN.md
- docs/workflow/changelog/2026-07.md

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py" -> PASS
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_*.py" -> PASS

## Rollback
Restore deleted docs from git history if a legacy document lookup is unexpectedly required.

## Completion Notes
- Removed three superseded documents.
- Updated workflow references to point to active playbook and skill contract.