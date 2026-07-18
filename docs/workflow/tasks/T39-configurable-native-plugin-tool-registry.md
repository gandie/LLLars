# T39 Configurable Native and Plugin Tool Registry

## Metadata
- Status: Proposed
- Priority: P1
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

## Objective
Implement configurable native tools and local plugin tool loading with safety controls.

## Scope
- Native tool toggles with allow/deny rules.
- Plugin discovery and registration from local paths.
- Duplicate/missing/unsafe plugin diagnostics.

## Non-Goals
- No remote plugin marketplace.
- No dynamic code download.

## Target Files
- lllars_core/tools/registry.py
- lllars_core/tools/native.py
- lllars_core/tools/plugins.py
- lllars_core/config/tools_section.py
- lllars_core/agent_builder.py
- tests/test_config.py
- tests/test_agent_builder.py

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_config.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_agent_builder.py"
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"

## Rollback
Fallback to built-in fixed native toolset.

## Completion Artifact
Deterministic tool-registration tests for native and plugin modes.
