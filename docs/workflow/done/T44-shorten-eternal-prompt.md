# T44 Shorten Eternal Prompt

## Metadata
- Status: Done
- Priority: P2
- Owner: Friday
- Created: 2026-07-18
- Updated: 2026-07-18

## Objective
Reduce the workflow eternal prompt to a concise startup sequence that avoids redundancy with skill and agent wiring.

## Scope
- Replace verbose eternal prompt text with a short four-step prompt.
- Keep one explicit nudge to prefer codebase MCP analysis over broad file-by-file reading.

## Non-Goals
- No changes to skill definitions.
- No changes to runtime or test behavior.

## Target Files
- docs/workflow/README.md

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py" -> PASS

## Rollback
Restore the previous prompt block from git history if broader procedural detail is needed.

## Completion Notes
- Eternal prompt now contains only four concise lines aligned with operator intent.