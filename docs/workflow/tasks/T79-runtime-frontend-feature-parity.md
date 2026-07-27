# T79 Runtime Frontend Feature Parity

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-27

## Why Needed
The runtime UI does not fully expose all available runtime configuration fields, which creates operator blind spots and API/UI drift.

## Objective
Update the runtime frontend to support all currently available runtime features and configuration knobs exposed by the payload contract.

## Scope
- Audit current JobSpec/run payload fields versus UI controls.
- Add missing UI controls for supported fields.
- Ensure payload serialization and null/optional handling align with API models.
- Add/extend tests for UI payload shaping and runtime submission behavior.

## Non-Goals
- No backend contract expansion in this task.
- No styling-overhaul effort beyond required usability updates.

## Target Files
- lllars_core/static/runtime/index.html
- lllars_core/runtime/models.py
- tests/test_runtime_api_submission.py
- tests/test_runtime_api_surface.py
- docs/runtime_api.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Revert UI control additions and restore prior payload-shaping behavior.

## Completion Artifact
UI exposes all supported runtime controls with passing submission/surface tests.