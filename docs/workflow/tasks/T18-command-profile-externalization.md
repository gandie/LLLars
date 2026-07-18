# T18 Command Profile Externalization

## Metadata
- Status: Ready
- Priority: P1
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

## Objective
Make command profiles extensible without code edits.

## Scope
- Add optional external profile source (JSON/YAML) merged with built-in profiles.
- Add duplicate/override conflict validation.
- Add diagnostics for missing requested profile.

## Non-Goals
- No role-based policy engine.
- No remote profile fetching.

## Target Files
- lllars_core/config/loader.py
- playground.example.json
- README.md
- tests/test_config.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_config.py"
- .\\venv\\Scripts\\python.exe .\\lllars.py --config .\\playground.example.json --prompt "profile externalization smoke"

## Rollback
Fall back to built-in registry when external profile loading fails.

## Completion Artifact
External profile example and passing config tests.
