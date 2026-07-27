# T77 Design Doc Hub And Chapter Split

## Metadata
- Owner: unassigned
- Created: 2026-07-27
- Updated: 2026-07-27

## Why Needed
DESIGN.md is near boundary pressure and has become harder to maintain; splitting into a hub and chapters improves navigability and lowers merge/boundary risk.

## Objective
Convert DESIGN.md into a concise hub document that links to chapter files under docs/design/ while preserving current design content and truth hierarchy.

## Scope
- Create docs/design/ chapter files covering current DESIGN.md sections.
- Replace DESIGN.md with a stable hub/navigation surface linking chapters.
- Update docs index references to ensure discoverability.
- Keep boundary compliance across markdown files.

## Non-Goals
- No behavior/runtime changes.
- No design policy changes beyond structural split.

## Target Files
- docs/DESIGN.md
- docs/design/
- docs/README.md
- tests/boundary_checks/markdown_boundaries.json

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Rollback
Restore single-file DESIGN.md and remove docs/design/ chapters.

## Completion Artifact
DESIGN.md acts as a hub with valid links to chapterized content and markdown boundary tests pass.