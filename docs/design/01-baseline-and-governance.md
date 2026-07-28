# Baseline and Governance

## North Star
LLLars reduces chaos in agentic coding by making orchestration explicit,
predictable, and operator-controlled.

## Document Status
This design chapter set is a governance reference, not a substitute for runtime
evidence.

When statements here conflict with observed behavior, follow the hierarchy of
truth and treat runtime behavior as authoritative.

## Current Baseline
- Runtime controls rely on native PydanticAI capabilities (usage limits,
  retries, tool timeout, instrumentation).
- Environment-aware execution is explicit (OS, shell, project-root context,
  allowlisted shell commands).
- MCP support is config-driven with preflight validation.
- Runtime service mode is active with HTTP job lifecycle endpoints and static
  operator UI.
- Runtime package boundaries are split by concern (`runtime/`, `config/`,
  `mcp/`, `tools/`) with compatibility removed in favor of canonical package
  imports.
- Queue backend support is currently productioned for `inmemory`; `redis`
  remains a scaling-path item.

## Governance and Decision Rules
- Human operator has veto at all times.
- Operator instructions override model habits and assumptions.
- Execution discipline: slow is fast; clarity before edits.
- Truth hierarchy:
  1. Running code and verified runtime behavior.
  2. Repository docs and design docs.
  3. Human discussion and intent framing.
  4. Agent internal reasoning.
  5. Any non-repo memory or cached context (lowest trust).

## Autonomy Boundary (Current)
In scope:
- Operator-guided config adaptation through pre-flight guidance.

Out of scope for now:
- Autonomous code self-modification.
- Unattended widening of safety boundaries.

Guardrail:
- Execution and safety policy changes require explicit human confirmation
  outside sandbox experiments.
