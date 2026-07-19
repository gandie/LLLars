# T33 Scheduling and Triggering Design Prep

## Metadata
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

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
- Design review against runtime package seams.

## Rollback
Keep submit-only lifecycle and remove draft contract references.

## Completion Artifact
Approved design contract for T34-T36.
