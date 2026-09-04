---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-09-04
  verdict: accepted
  would_delegate_similar_again: true

  score_scale:
    min: 1
    max: 5
    meaning:
      1: poor
      3: acceptable
      5: excellent

  outcome:
    correctness:
    scope_discipline:
    validation_trust:

  collaboration:
    ambiguity_handling:
    operator_load:
    trust_delta:

  notes: >
    HUMAN NOTES
---

# T90 OpenAI-Compatible Model Probe Auth

## Metadata
- Owner: unassigned
- Created: 2026-09-04
- Updated: 2026-09-04

## Why Needed
OpenAI-compatible startup model preflight probes call `/v1/models` without passing the configured `OPENAI_API_KEY`, causing authenticated providers to fail startup with `401 Unauthorized` before pydantic_ai provider construction can use the environment credential.

## Objective
Allow authenticated OpenAI-compatible model-listing preflight probes to use the standard bearer token from `OPENAI_API_KEY` while preserving unauthenticated Ollama and local-provider behavior.

## Scope
- Add bearer-token request headers for OpenAI-compatible startup model probes.
- Keep Ollama startup probes unchanged.
- Preserve strict OpenAI profile compatibility with the installed pydantic_ai profile mapping shape.
- Document `OPENAI_API_KEY` as the CLI and Docker runtime credential channel.
- Add focused regression coverage for authenticated and unauthenticated probe paths.

## Non-Goals
- No config schema changes.
- No new CLI flags.
- No provider-specific credential registry beyond `OPENAI_API_KEY` for OpenAI-compatible probes.

## Target Files
- .env.runtime.example
- docs/configuration.md
- docs/docker_runtime.md
- lllars_core/openai_compat.py
- lllars_core/mcp/model_probe.py
- lllars_core/mcp/model_probe_support.py
- tests/test_agent_builder.py
- tests/test_mcp_model_probe.py

## Verification
- PASS `./venv/bin/python -m unittest discover -s tests -p "test_mcp_model_probe.py"`
- PASS `./venv/bin/python -m unittest discover -s tests -p "test_agent_builder.py"`
- PASS `./venv/bin/python -m unittest discover -s tests -p "test_refactor_boundaries.py"`
- PASS `./venv/bin/python -m unittest discover -s tests -p "test_markdown_boundaries.py"`
- PASS `./venv/bin/python -m unittest discover ./tests/` (142 tests)

## Rollback
Revert the model probe request-header changes, strict OpenAI profile compatibility repair, docs updates, and focused model-probe tests.

## Completion Artifact
OpenAI-compatible startup model probes include `Authorization: Bearer <OPENAI_API_KEY>` when the environment variable is present, with targeted and full-suite tests passing.

## Completion Notes
- Added OpenAI-compatible probe request headers in `lllars_core/mcp/model_probe.py` using `OPENAI_API_KEY` from the process environment.
- Kept `lllars_core/mcp/model_probe_support.py` focused on request execution and payload parsing while preserving unauthenticated Ollama behavior.
- Fixed `lllars_core/openai_compat.py` for the installed pydantic_ai dict-shaped `OpenAIModelProfile` so strict OpenAI flags are actually retained.
- Documented `OPENAI_API_KEY` for CLI and Docker runtime use in `.env.runtime.example`, `docs/configuration.md`, and `docs/docker_runtime.md`.