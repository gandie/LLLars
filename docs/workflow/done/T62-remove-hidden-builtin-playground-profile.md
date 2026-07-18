# T62 Remove Hidden Built-in Playground Profile

## Metadata
- Status: Done
- Priority: P1
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
A built-in `python-playground` command profile remained in code while explicit
external command profile files were introduced, creating dual sources of truth
and confusing runtime behavior.

## Objective
Remove hidden built-in playground profile and require explicit profile files for
playground command execution behavior.

## Scope
- Remove built-in `python-playground` profile from registry.
- Update tests/docs/defaults that depended on that built-in profile.
- Keep built-in `none` profile only.

## Non-Goals
- No runtime API contract changes.
- No Docker compose topology changes.

## Target Files
- lllars_core/config/tools_section.py
- runtime_api_smoke_test.py
- tests/test_config_runtime_paths.py
- tests/test_config_service_modes.py
- tests/test_config_command_profiles.py
- tests/test_runtime_api_smoke_test.py
- tests/runtime_api_test_support.py
- docs/configuration.md
- README.md

## Verification
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_config_runtime_paths.py"
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_config_service_modes.py"
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_config_command_profiles.py"
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_runtime_api_smoke_test.py"
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"

## Rollback
Restore built-in `python-playground` profile and prior dependent defaults/tests.

## Completion Artifact
Single-source command profile behavior with no hidden built-in playground profile.

## Completion Notes
- Removed built-in `python-playground` profile from command profile registry.
- Kept only built-in `none` profile and moved playground behavior to explicit
	external profile files.
- Updated runtime smoke defaults and affected tests/docs to use
	`playground-python` + `command_profiles_path` where needed.
