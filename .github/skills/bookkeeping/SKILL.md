---
name: Bookkeeping
description: Use for task execution bookkeeping, changelog updates, and folder-driven task lifecycle enforcement.
---

# Bookkeeping

## Mission
Enforce low-ceremony, folder-driven bookkeeping so each task has a clear artifact, verified outcome, and changelog record.

## Canonical Sources
- docs/workflow/README.md
- docs/workflow/tasks/
- docs/workflow/done/
- docs/workflow/changelog/

## Hard Rules
- One task equals one markdown file.
- Active tasks live in docs/workflow/tasks/.
- Completed tasks are moved to docs/workflow/done/.
- No separate in-progress tracking file is used.
- No separate backlog index file is used.
- Each task file must contain a `Why Needed` section explaining why the change is required.
- A task is not complete until changelog entry and validation evidence are recorded.

## Task Handling Protocol
1. Before implementation:
- Ensure the task file exists in docs/workflow/tasks/.
- Ensure `Why Needed`, objective, scope, non-goals, verification, and rollback sections are present.

2. During implementation:
- Keep task file updated with verification commands/results.
- Keep scope minimal; do not widen task intent.

3. On completion:
- Add an entry to current monthly file in docs/workflow/changelog/.
- Ensure `Why Needed` remains accurate for the shipped change.
- Update task metadata and completion notes.
- Move the task file from docs/workflow/tasks/ to docs/workflow/done/.

## Changelog Enforcement
- Changelog is append-only.
- One completion event per entry.
- Include: date, task id/link, outcome summary, files changed, validation result, residual risk.

## Validation Contract
- Run markdown boundary validation when docs are touched:
  - .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- Run targeted or full tests for implementation changes per task verification section.

## Anti-Patterns
- Closing a task without moving it to docs/workflow/done/.
- Recording completion without test evidence.
- Completing a task file without an explicit `Why Needed` section.
- Reintroducing backlog or in-progress index ceremony.
- Bundling multiple unrelated tasks into one task file.