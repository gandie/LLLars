# T54 Move Boundary Configs To Tests

## Metadata
- Status: Completed
- Priority: P1
- Owner: Copilot
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Boundary governance artifacts are test-side concerns and should live with boundary tests, not in docs.

## Objective
Move markdown and refactor boundary config JSON files from docs to tests and rewire references.

## Scope
- Move `docs/markdown_boundaries.json` to tests folder.
- Move `docs/refactor_boundaries.json` to tests folder.
- Update boundary tests to use new config paths.

## Non-Goals
- No changes to boundary defaults or waiver semantics.
- No runtime behavior changes.

## Target Files
- docs/markdown_boundaries.json
- docs/refactor_boundaries.json
- tests/boundary_checks/*.json
- tests/test_markdown_boundaries.py
- tests/test_refactor_boundaries.py

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"

## Rollback
Move the config files back into docs and restore previous test config paths.

## Completion Notes
- Moved boundary config files from docs into `tests/boundary_checks`.
- Updated boundary tests to load configs from the new test-side paths.
- Removed old config files from docs.

## Validation Evidence
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py" -> OK (1 test)
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" -> OK (1 test)
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -> OK (54 tests)
- get_errors -> No errors found
