# T19 Provider-Aware Startup Preflight

## Metadata
- Status: Done
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
- Leverage pydantic_ai provider wrappers - check docs!

## Non-Goals
- No provider SDK integration.

## Target Files (Check! Might be stale pointers!)
- lllars_core/mcp/model_probe.py
- lllars_core/mcp/model_probe_support.py
- tests/test_mcp_model_probe.py
- docs/configuration.md
- README.md

## Verification
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_mcp_model_probe.py"
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\
- PASS: .\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"

## Rollback
Keep existing Ollama probe as default fallback.

## Completion Artifact
Updated preflight docs with multi-provider examples.

## Completion Notes
- Implemented provider-family inference for startup model probe using
	pydantic_ai-style model prefixes (`<provider>:<model>`), with backward
	compatible Ollama default when no explicit provider prefix exists.
- Added provider-specific probe strategies:
	- Ollama: `.../api/tags` with `models[].name`
	- OpenAI-compatible: `.../v1/models` with `data[].id`
- Added structured warning mode when OpenAI-compatible model listing is
	unsupported, instead of hard failing startup preflight.
- Added dedicated tests for provider-aware probe behavior and unsupported
	listing warning mode.
