# T76 Plugin Tool Example Wiring

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-27

## Why Needed
Operators need a concrete, working plugin-tool example to reduce setup friction and prove local plugin wiring end-to-end.

## Objective
Add a minimal local plugin tool example and wire it through playground config so plugin extensibility is demonstrable without code archaeology.

## Scope
- Add a minimal plugin module under playground/plugins with register_tools(agent, cfg, tool_error).
- Wire run.tool_plugins.paths in playground.example.json to include the example plugin path.
- Document usage in operator-facing docs with a minimal invocation example.
- Add focused tests for plugin discovery/registration success path.

## Non-Goals
- No plugin sandboxing redesign.
- No remote plugin loading.
- No broader tool registry semantics changes.

## Target Files
- playground.example.json
- playground/plugins/
- lllars_core/tools/plugins.py
- tests/test_tool_registry.py
- README.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Remove plugin example files and revert playground config/plugin docs wiring.

## Completion Artifact
Config example shows plugin path, tests pass, and docs contain a copy-paste plugin example flow.