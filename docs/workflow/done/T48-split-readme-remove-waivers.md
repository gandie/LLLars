# T48 Split README and Remove Waivers

## Metadata
- Status: Done
- Priority: P1
- Owner: Friday
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
The root README had waiver-based boundary exceptions and mixed multiple concerns in one large file. This made documentation harder to maintain and increased risk of stale operational guidance.

## Objective
Split root README into focused docs, remove README boundary waivers, and clean stale guidance.

## Scope
- Replace root README with concise overview and links.
- Add focused docs pages in `docs/`.
- Remove README waivers from markdown boundary config.
- Ensure stale config copy step (`lllars.example.json`) is removed from user-facing guidance.

## Non-Goals
- No runtime behavior changes.
- No API contract changes.

## Target Files
- README.md
- docs/README.md
- docs/configuration.md
- docs/runtime_api.md
- docs/docker_runtime.md
- docs/markdown_boundaries.json

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py" -> PASS
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_*.py" -> PASS

## Rollback
Restore prior README and waiver config from git history if documentation consumers require the old monolithic layout.

## Completion Notes
- Root README is now concise and points to docs pages by concern.
- README waiver entries were removed from boundary configuration.
- Documentation now uses shipped example configs (`playground.split.example.json`) instead of removed `lllars.example.json` copy flow.