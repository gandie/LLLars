# LLLars Workflow Bookkeeping

## Purpose
This folder is the canonical bookkeeping surface for implementation work.

## File Map
- `tasks/`: active and queued task files.
- `done/`: completed task files moved from `tasks/`.
- `changelog/`: append-only change log files.

## Operating Rules
1. Update task file first, including an explicit `Why Needed` section.
2. Run implementation and validations.
3. Run full suite and confirm pass: `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`.
4. Append changelog entry.
5. Move completed task file from `tasks/` to `done/`.

Folder location is the only status protocol:
- `tasks/` means active.
- `done/` means complete.

No protocol extension is allowed:
- Do not add lifecycle metadata fields such as `Status` or `Priority` to task files.

## Mandatory Task Template

```markdown
# TXX Short Task Title

## Metadata
- Owner: unassigned
- Created: YYYY-MM-DD
- Updated: YYYY-MM-DD

## Why Needed
<Why this change is required>

## Objective
<Expected outcome>

## Scope
- <In-scope item>

## Non-Goals
- <Out-of-scope item>

## Target Files
- <path/to/file>

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\

## Rollback
<Rollback plan>

## Completion Artifact
<What proves completion>
```

This file and the bookkeeping skill define the active workflow contract.

## Bookkeeping Skill
Use skill definition at `.github/skills/bookkeeping/SKILL.md` for task handling and completion enforcement.

## Eternal Prompt
Use this prompt at the start of any task session:

```text
Look at task.
Understand task, preferring codebase MCP analysis tools over broad file-by-file reading.
Ask clarifying questions if needed.
Proceed to implementation.
```