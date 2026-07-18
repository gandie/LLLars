## 9. Evaluation Metrics
A lightweight scorecard for whether the bootstrap is working:
- Scope adherence: percent of runs without out-of-scope edits.
- Validation completeness: percent of runs with explicit verification.
- Rework rate: follow-up fixes needed per task.
- Clarification quality: blockers caught before edits.
- Onboarding speed: time to productive first task in a new repo.

Add eval-specific indicators:
- Eval pass rate by facet (outcome/process/policy/regression/stress).
- Eval drift rate: how often thresholds/waivers expand without planned removal.
- Regression catch rate: percent of failures caught by evals before merge.
- Boundary compliance trend: file/routine complexity violations over time.
- Mean time to restore green eval suite after refactor changes.
- Guidance harvest rate: meaningful struggles converted into durable artifacts.
- Repeated-struggle rate: how often the same friction recurs after guidance updates.
- Error-to-learning latency: time from meaningful failure detection to merged guidance/eval update.

## 9.1 Relational Governance Layer
Humans naturally form social bonds with tools and teammates, including AI operators.
This is neither inherently good nor bad. It is an execution factor that must be governed.

Goal:
- Preserve morale, continuity, and team cohesion benefits from ritualized interaction.
- Prevent emotional framing from replacing technical evidence or operator authority.

Normative policy:
- MUST keep decision authority with the human operator.
- MUST ground implementation claims in artifacts (tests, logs, boundary checks, code diffs).
- MUST NOT use emotional language as technical evidence (for example "trust me" or loyalty framing).
- MUST NOT use guilt, pressure, or social obligation framing to influence approval decisions.
- SHOULD allow bounded ritual language at run boundaries (kickoff, handoff, completion).
- SHOULD separate celebration from risk decisions by requiring explicit evidence blocks before approval.

Operational controls:
- Relational contract: repository states explicit roles (human decides, agent executes).
- Ritual channel: approved celebratory language list and allowed moments of use.
- Evidence gate: high-risk changes require explicit verification outputs before merge.
- Second-source checks: high-risk tasks require independent validation path (test suite, evals, or peer run).
- Rotation check: periodically vary agent mode/persona for critical workflows to reduce over-attachment.

Evaluation hooks (machine-checkable where possible):
- Process eval: completion notes include an evidence section with commands and outcomes.
- Policy eval: fail run if approval rationale lacks artifact references.
- Language eval: flag persuasion-only rationale in handoff text (no test/log/diff references).
- Regression eval: compare post-change incident/rework rates after "high-confidence" handoffs.

Relational retro block (for major tasks):
1. What relational or ritual elements improved execution quality?
2. What relational framing increased bias or reduced scrutiny?
3. What policy or eval update prevents repeat failure?
4. What should remain unchanged because it improved coordination?

Anti-patterns to explicitly reject:
- "The agent sounded confident" as a merge criterion.
- "We always do it this way with this persona" replacing verification.
- Social pressure to skip checks during celebration moments.
- Operator deferring final judgment to agent tone instead of evidence.

[<- Previous: Risks and Mitigations](./09-risks-and-mitigations.md) | [Index](./index.md) | [Next: Standardization Pattern ->](./11-standardization-pattern.md)
