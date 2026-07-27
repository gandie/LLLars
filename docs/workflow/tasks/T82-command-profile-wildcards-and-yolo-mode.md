# T82 Command Profile Wildcards And Yolo Mode

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-27

## Why Needed
Operators requested more flexible shell command profile behavior for dynamic workflows.

## Objective
Add wildcard command-profile resolution and yolo mode semantics with explicit safety boundaries and full validation coverage.

## Scope
- Implement wildcard resolution semantics for command profiles.
- Implement yolo mode according to operator-approved contract.
- Preserve observability and safety diagnostics for resolved commands.
- Add comprehensive config/runtime tests and docs updates.

## Non-Goals
- No unrestricted shell execution by default.
- No changes to unrelated runtime scheduling or MCP behavior.

## Ambiguity Gates
- Yolo model: confirm whether yolo is a profile name, boolean flag, or both.
- Safety semantics: confirm whether yolo bypasses allowlist or only broadens profile selection.
- Wildcard domain: confirm matching target (profile names only vs command strings too).
- Pattern syntax: confirm glob-only vs regex support.
- Conflict behavior: confirm deterministic precedence when multiple wildcard matches occur.

## Target Files
- lllars_core/config/tools_section.py
- lllars_core/runtime/settings.py
- lllars_core/config/models.py
- tests/test_config_command_profiles.py
- tests/test_runtime_runner_overrides.py
- docs/configuration.md
- README.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert wildcard/yolo parsing and restore strict named profile semantics.

## Completion Artifact
Wildcard and yolo behavior is explicitly defined, safety-bounded, tested, and documented.