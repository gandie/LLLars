---
name: Forcing Line Development
description: Use for ambiguity-heavy development decisions by generating candidate moves, selecting the most forcing validated line, and blocking speculative drift.
---

# Forcing Line Development

## Mission
Apply chess-style forcing-line reasoning to software work: generate candidate moves, calculate consequences, reject speculative branches, and execute only the minimal winning line.

## Use When
- Early design where contracts are underspecified.
- Implementation planning with multiple plausible paths.
- Refactor decisions with risk of scope creep.
- Incident response where quick-but-wrong branching is costly.
- Any task where ambiguity could cause speculative overengineering.

## Core Loop
1. Define position:
- Restate objective, constraints, and explicit non-goals.
- Separate known facts from assumptions.

2. Generate candidate moves:
- Produce 2 to 4 viable options.
- Keep each option concrete and minimal.

3. Calculate forcing lines:
- For each option, trace likely downstream effects.
- Prefer lines that reduce ambiguity and keep reversibility high.
- Disqualify lines that require speculative policy semantics.

4. Ambiguity gate:
- If multiple interpretations remain valid, stop.
- Ask one focused operator question that resolves the branch.
- Do not edit code or contracts until resolved.

5. Execute minimal winning line:
- Implement only the selected line.
- Avoid opportunistic expansions.

6. Verify and close:
- Run defined validations.
- Record residual risk and deferred branches explicitly.

## Hard Rules
- Ambiguity is blocking, not advisory.
- No speculative defaults for unspecified policy dimensions.
- No structure inflation when scalar/opaque representation satisfies scope.
- Do not mix branch resolution and implementation in the same step.
- If a line needs future assumptions to look good, reject it.

## Early Design Contract Rules
- Prefer minimal contracts first: opaque fields before strategy hierarchies.
- Encode only invariants explicitly requested or already proven by runtime behavior.
- Keep examples type-correct with declared schema fields.
- Document deferred semantics as future work, not current contract behavior.

## Output Pattern
When reporting decision work, use this compact pattern:
- Position: objective, constraints, non-goals.
- Candidates: option A/B/C in one line each.
- Forcing line chosen: selected option and why it dominates.
- Blockers: one clarification question if ambiguity remains.
- Execution scope: exact files/symbols to change.

## Anti-Patterns
- Solving unasked future problems.
- Expanding scope because a pattern is familiar.
- Conflating plausibility with necessity.
- Hiding assumptions inside defaults, examples, or validators.
- Continuing implementation while ambiguity is unresolved.
