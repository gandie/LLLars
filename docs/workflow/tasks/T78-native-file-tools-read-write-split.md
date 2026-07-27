# T78 Native File Tools Read Write Split

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-27

## Why Needed
Current native_files group couples read and write operations; least-privilege operation requires the ability to run read-only agents.

## Objective
Introduce finer native file tool group controls so agents can be configured for read-only file access without write capability.

## Scope
- Add granular tool-group options for file-read and file-write capability separation.
- Preserve backward compatibility for existing native_files configurations.
- Update registry/config validation and documentation.
- Add tests for read-only, write-enabled, and compatibility paths.

## Non-Goals
- No shell-policy semantic changes.
- No plugin or MCP behavior redesign.

## Target Files
- lllars_core/tools/registry.py
- lllars_core/tools/native.py
- lllars_core/config/tool_registry_section.py
- lllars_core/config/models.py
- tests/test_tool_registry.py
- tests/test_config.py
- docs/configuration.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert to coarse native_files grouping and remove new granular group references.

## Completion Artifact
Config can express read-only native file tool mode, behavior is test-covered, and legacy configs still function.