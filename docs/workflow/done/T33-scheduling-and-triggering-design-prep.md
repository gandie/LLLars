# T33 Scheduling and Triggering Design Prep

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-19

## Why Needed
Runtime package seams are now stable enough to define scheduling and trigger metadata contracts without introducing scheduler behavior. Locking these contracts early reduces API and model churn across follow-up slices T34-T36.

## Objective
Define stable contracts for deadlines, schedules, and trigger sources on top of runtime package boundaries.

## Scope
- Terminology and lifecycle states for timed/scheduled/triggered jobs.
- Data contracts for `deadline_at`, `run_at`, `schedule`, `trigger_source`.
- Compatibility notes for immediate-submit flow.

## Non-Goals
- No endpoint additions.
- No scheduler loop implementation.

## Target Files
- docs/DESIGN.md
- docs/workflow/tasks/T33-scheduling-and-triggering-design-prep.md
- lllars_core/runtime/models.py

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Keep submit-only lifecycle and remove draft contract references.

## Completion Artifact
Approved design contract for T34-T36.

## Completion Notes
- Added schema-level scheduling and trigger fields to `JobSpec`: `deadline_at`, `run_at`, `schedule`, and `trigger_source`.
- Added `TriggerSource` contract type to keep runtime boundary definitions explicit.
- Added contract invariants for mutually exclusive timing controls and scheduled-trigger consistency.
- Updated design documentation with lifecycle terms, field semantics, invariants, and immediate-submit compatibility notes.
- Follow-up correction: removed timezone mechanics from the prep contract to keep scope minimal (no `schedule.timezone` field and no timezone-aware datetime constraint in `JobSpec`).
- Follow-up correction: removed cron-specific schedule shape (`kind: "cron"`) and kept `schedule` as a plain string expression for simple scheduling.
- Strategy direction clarified: `schedule` is an opaque strategy selector/expression (for example, `carbon-aware`) paired with deadlines and external trigger sources, with cron as optional future strategy rather than primary target.
- Validation results:
	- PASS `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
	- PASS `.\venv\Scripts\python.exe -m unittest discover .\tests\`
