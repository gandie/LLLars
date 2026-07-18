# T53 Move Boundary Checkers Out Of Core

## Metadata
- Status: Completed
- Priority: P1
- Owner: Copilot
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Boundary-check logic is test/governance concern and should not live inside lllars_core runtime package.

## Objective
Move markdown and python boundary checker modules from lllars_core to test-side modules and rewire boundary tests accordingly.

## Scope
- Relocate lllars_core.markdown_boundaries to tests package.
- Relocate lllars_core.refactor_boundaries to tests package.
- Update test imports and ensure all boundary/full tests pass.

## Non-Goals
- No changes to boundary rule semantics.
- No runtime feature changes.

## Target Files
- lllars_core/markdown_boundaries.py
- lllars_core/refactor_boundaries.py
- tests/test_markdown_boundaries.py
- tests/test_refactor_boundaries.py
- tests/boundary_checks/*

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"

## Rollback
Restore original module locations in lllars_core and revert imports.

## Completion Notes
- Moved boundary checker modules from `lllars_core` to `tests/boundary_checks`.
- Rewired boundary tests to import from `boundary_checks` package.
- Removed `lllars_core/markdown_boundaries.py` and `lllars_core/refactor_boundaries.py`.
- Kept boundary checker behavior unchanged; only module location/import wiring changed.

## Validation Evidence
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py" -> OK (1 test)
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py" -> OK (1 test)
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -> OK (54 tests)
- get_errors -> No errors found
