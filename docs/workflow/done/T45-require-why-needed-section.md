# T45 Require Why Needed Section

## Metadata
- Status: Done
- Priority: P1
- Owner: Friday
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
Completion notes explain what changed, but they do not always capture the motivation for the change. A dedicated rationale section preserves decision context and helps future maintainers evaluate regressions, reversions, and related follow-up work.

## Objective
Make `Why Needed` a mandatory section in task handling rules.

## Scope
- Update bookkeeping skill rules and protocol.
- Update AGENTS baseline bookkeeping checks.
- Update workflow playbook operating rules.

## Non-Goals
- No runtime behavior changes.
- No service or API changes.

## Target Files
- .github/skills/bookkeeping/SKILL.md
- AGENTS.md
- docs/workflow/README.md

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py" -> PASS
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_*.py" -> PASS

## Rollback
Revert the rule updates if operator policy changes.

## Completion Notes
- Bookkeeping skill now requires `Why Needed` and enforces it in protocol checks.
- AGENTS bookkeeping stop-check now requires rationale alongside completion and validation.
- Workflow playbook operating rules now call out `Why Needed` explicitly.