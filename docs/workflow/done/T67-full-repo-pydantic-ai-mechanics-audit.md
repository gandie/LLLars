# T67 Full Repo PydanticAI Mechanics Audit

## Metadata
- Owner: unassigned
- Created: 2026-07-18
- Updated: 2026-07-18

## Why Needed
After migrating startup model probing to pydantic_ai-native parsing, we need a full-repository audit to identify remaining custom patterns that duplicate or bypass pydantic_ai mechanics, so we can prevent further drift.

## Objective
Complete a docs-first, full-repo scan and produce prioritized refactor targets and guardrails to keep model/provider behavior aligned with pydantic_ai.

## Scope
- Map all pydantic_ai integration points in runtime and preflight paths.
- Identify custom logic duplicating model/provider/retry/tooling mechanics.
- Propose a staged anti-growth plan with minimal-risk adoption order.

## Non-Goals
- No broad runtime behavior change in this audit-only task.
- No provider feature expansion beyond pydantic_ai support.

## Target Files
- lllars_core/agent_builder.py
- lllars_core/mcp/model_probe_support.py
- lllars_core/mcp/model_probe.py
- lllars_core/mcp/loader.py
- lllars_core/runtime/runner_single.py
- docs/configuration.md
- README.md

## Verification
- .\venv\Scripts\python.exe -m unittest discover .\tests\

## Findings
- High: Runtime model construction is still provider-hardcoded to Ollama in `lllars_core/agent_builder.py` (`OllamaModel` + `OllamaProvider`), with custom parsing helpers `parse_ollama_model` and `normalize_ollama_base_url`.
- High: Config loading still requires explicit `provider_url` for non-serve mode (`lllars_core/config/loader_steps.py`), preventing native provider default behavior (provider env/default endpoint resolution) from being used.
- Medium: Startup preflight probing now uses native provider parsing, but listing logic remains custom endpoint strategy (`/api/tags` and `/v1/models`) in `lllars_core/mcp/model_probe_support.py`; this is currently acceptable as best-effort preflight, but should remain explicitly scoped.
- Low: Project docs continue to emphasize Ollama/OpenAI-compatible probe examples (`docs/configuration.md`, `README.md`), which can still bias future contributions toward endpoint-level custom mechanics.

## Recommended Implementation Slices
1. Slice A (highest priority): Replace hardcoded Ollama runtime model build path with pydantic_ai-native model inference (`infer_model`) and provider-aware factory wiring.
2. Slice B: Relax config requirement for explicit `provider_url` when selected provider can resolve defaults natively (while preserving explicit override support).
3. Slice C: Keep preflight as optional best-effort connectivity/model-presence check; avoid expanding custom provider family heuristics.
4. Slice D: Add boundary-style guard tests that fail if new custom provider-prefix taxonomies or URL-shape inference logic are introduced.
5. Slice E: Update operator docs to state runtime provider support from resolved pydantic_ai model/provider selection, not handcrafted endpoint categories.

## Rollback
No runtime rollback needed for an audit-only task.

## Completion Artifact
Completed full-repo, docs-first pydantic_ai mechanics audit with severity-ranked findings and a staged anti-growth plan.