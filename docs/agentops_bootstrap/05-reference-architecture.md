## 4. Reference Architecture
AgentOps Bootstrap separates control from execution.

### 4.1 Control Plane
- Governance document (for example AGENTS.md).
- Custom agent definition (for example Friday).
- Skill files with domain constraints and references.
- Task backlog and completion contracts.

### 4.2 Execution Plane
- Concrete implementation loops run by agents.
- Tooling selection under explicit policy.
- Validation commands and outcomes.
- Artifacted outputs and handoff notes.
- Eval runs that continuously test quality, process compliance, and regressions.

### 4.3 Evaluation Plane (Agent Evals)
The evaluation plane operationalizes quality and governance as executable checks.

Core eval facets:
- Outcome evals: did the task complete correctly?
- Process evals: did the agent follow required steps and constraints?
- Policy evals: were architectural boundaries and safety rules respected?
- Regression evals: did behavior remain stable after prompt/tool/code changes?
- Stress evals: does behavior remain acceptable under ambiguity and partial failure?

Meta-pattern eval expectation:
- When meaningful execution struggle occurs, runs should produce a short retro artifact and a concrete guidance update proposal.
- Error episodes should include learning capture (what failed, why, what was updated to prevent repeat).

In practice, these evals should be repository-native (tests/scripts/config), versioned,
and required in the same run loop as functional tests.

[<- Previous: Design Principles](./04-design-principles.md) | [Index](./index.md) | [Next: Bootstrap Sequence ->](./06-bootstrap-sequence.md)
