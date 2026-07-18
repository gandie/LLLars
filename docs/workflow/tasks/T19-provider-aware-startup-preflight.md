# T19 Provider-Aware Startup Preflight

## Metadata
- Status: Deferred
- Priority: P2
- Owner: unassigned
- Created: 2026-07-16
- Updated: 2026-07-18

## Objective
Expand model endpoint probing beyond Ollama-only assumptions.

## Scope
- Provider family inference (Ollama vs OpenAI-compatible).
- Probe strategy per provider family.
- Structured warning mode when model listing is unsupported.

## Non-Goals
- No provider SDK integration.
- No authentication redesign.

## Target Files
- lllars_core/mcp/preflight.py
- lllars_core/config/loader.py
- tests/test_config.py
- README.md

## Verification
- .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_config.py"
- .\\venv\\Scripts\\python.exe .\\lllars.py --config .\\playground.example.json --prompt "provider preflight smoke"

## Rollback
Keep existing Ollama probe as default fallback.

## Completion Artifact
Updated preflight docs with multi-provider examples.
