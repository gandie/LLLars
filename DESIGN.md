# DESIGN

> Historical note: this document captures a previous orchestration direction.
> The current runtime has since migrated to native PydanticAI usage limits,
> retries, timeout, and instrumentation controls.

## Session Artifact

Date: 2026-06-20

This document captures the final design direction from this session, plus a concise summary of implemented ideas and their intent.

## Project North Star (Restated)

LLLars should reduce chaos in agentic coding by making tool orchestration explicit, predictable, and aligned with operator intent.

The practical interpretation for this session:
- Do not expose tools that are not usable in current config.
- Prefer low-risk orchestration controls over heavyweight automation.
- Keep operators informed at runtime about effective orchestration limits.

## Key Design Insight (Final Thought)

Instead of an automatic intent router that classifies user prompts and may guess wrong, introduce a pre-flight Task Wizard.

Task Wizard concept:
- Runs before agent execution.
- Guides human operators through task setup and harness balancing.
- Encodes accumulated knowledge on how to tune config for specific task types.
- Produces a concrete config profile for the upcoming run.
- Keeps decision authority with the human operator instead of hidden automatic classification.

Why this is preferable to naive intent routing:
- Lower surprise risk: no opaque misclassification.
- Better trust: operator sees and confirms knobs before execution.
- Better portability: wizard heuristics can evolve independently from core runtime loop.
- Better alignment with project pitch: explicit orchestration, not hidden magic.

## Conversation Summary

1. Tool visibility sharpening
- Problem identified: tools with missing config were still visible and produced runtime "not configured" no-ops.
- Change made: unconfigured tools are no longer registered in the agent tool schema.
- Outcome: fewer wasted tool calls, lower confusion, cleaner orchestration.

2. Low-risk orchestration controls (selected)
- Candidate list explored, but only low-risk items were accepted for implementation.
- Implemented:
  - Per-tool budgets (in addition to global budget).
  - Circuit breaker for repeated identical tool errors.
- Explicitly deferred:
  - Phase-based gating.
  - Automatic intent routing.

3. Operator runtime visibility
- Added startup runtime line that prints effective orchestration controls:
  - global tool budget
  - per-tool budgets
  - circuit breaker threshold
- Outcome: operators can validate active constraints immediately at run start.

## Implemented Behavior (Conceptual)

- Config-driven tool exposure
  - Only tools that are configured and usable are exposed to the running agent.

- Budget enforcement
  - Global tool call budget remains active.
  - Optional per-tool budgets enforce caps by tool name.

- Circuit breaker
  - If the same tool returns the same normalized error repeatedly up to threshold, that tool is disabled for the current run.

- Telemetry support
  - Runtime telemetry records per-tool budget exceed events and circuit breaker trips/disabled tools.

## Design Principles Confirmed

- Prefer explicit operator control over hidden automation.
- Prefer additive low-risk controls over complex orchestration state machines.
- Keep prompts, schema visibility, and runtime behavior aligned.
- Make the active policy observable to humans at execution time.

## Next Design Step (No Code Yet)

Design and prototype a pre-flight Task Wizard that:
- Asks a small set of task-scope questions.
- Recommends config values for tool visibility, budgets, shell allowlist, and breaker threshold.
- Shows trade-offs (speed vs safety vs autonomy) before run.
- Writes a selected config profile with clear provenance.

This keeps orchestration cleverness in a human-guided setup layer, while the runtime remains deterministic and robust.
