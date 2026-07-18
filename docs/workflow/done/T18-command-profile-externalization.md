# T18 Command Profile Externalization

## Metadata
- Status: Done
- Priority: P1
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

## Why Needed
Built-in command profiles required code edits for every profile change, which
slowed operator workflow and forced policy tweaks into runtime code changes.
External profile loading enables local profile extension while preserving safe
validation boundaries around duplicate names and unknown profile selection.

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
- lllars_core/config/loader_steps.py
- lllars_core/config/tools_section.py
- lllars_core/runtime/settings.py
- playground.example.json
- playground.command-profiles.yaml
- README.md
- tests/test_config_command_profiles.py
- tests/test_config_runtime_paths.py
- tests/test_runtime_runner_overrides.py

## Verification
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_config_runtime_paths.py"
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_config_command_profiles.py"
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_runner_overrides.py"
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- PASS: .\\venv\\Scripts\\python.exe .\\lllars.py --config .\\playground.example.json --timeout-sec 60 --prompt "Quick! Run tests in workspace!"
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\

## Rollback
Fall back to built-in registry when external profile loading fails.

## Completion Artifact
External profile example and passing config tests.

## Completion Notes
- Added `run.command_profiles_path` support for local JSON/YAML profile files.
- Merged external profiles with built-ins while rejecting built-in name
	conflicts.
- Added diagnostics context for unknown `command_profile` when an external
	source is configured.
- Added regression tests for JSON/YAML sources and conflict diagnostics.
- Fixed runtime command-profile revalidation so externally loaded profiles
	remain valid during job execution.
- Refactored tests/modules to satisfy refactor-boundary limits and revalidated
	the full repository test suite.
