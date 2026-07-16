# AgentOps Bootstrap

## Abstract
AgentOps Bootstrap is a practical method for turning ad-hoc AI-assisted coding into a governed engineering operating model. Instead of relying on prompt quality alone, it installs persistent control artifacts inside a repository: authority rules, execution discipline, tool policy, role-specialized agents, and domain skills. The result is lower variance between runs, clearer human oversight, and higher implementation reliability over time.

## 1. Problem Statement
Most AI coding workflows fail not because models are weak, but because execution is ungoverned. Common failure modes include:
- Prompt drift: behavior changes across sessions.
- Tool misuse: agents choose suboptimal or unsafe tools.
- Scope creep: unnecessary refactors and speculative abstractions.
- Ambiguous accountability: no explicit veto path or truth hierarchy.
- Knowledge loss: standards live in chat history instead of repo artifacts.

AgentOps Bootstrap addresses these by making execution policy explicit, versioned, and reusable.

## 2. Definition
AgentOps Bootstrap is the initial repository setup that establishes a durable control plane for agentic implementation.

It typically includes:
- Baseline governance rules (human authority, execution discipline, truth order).
- A primary custom implementation agent with invocation rules.
- Skill packs that encode domain-specific behavior and doc-first constraints.
- A task protocol for one-pass implementation loops.
- Agent evals that make quality and policy checks machine-readable.
- Consolidated planning docs that align scope, phases, and acceptance criteria.

Agent evals in this context are repeatable checks that verify both outcomes and execution behavior.
They convert expectations (scope, tool use, boundaries, safety) into deterministic pass/fail signals.

## 3. Design Principles
### 3.1 Human Sovereignty
The human operator owns decisions and can veto any action at any time.

### 3.2 Protocol Over Personality
Reliability comes from repository artifacts, not model mood or one-off prompt phrasing.

### 3.3 Slow Is Fast
Clarity before edits reduces rework, regressions, and hidden risk.

### 3.4 Truth Hierarchy
When facts conflict, prefer:
1. Running code and verified behavior.
2. Repository docs and design docs.
3. Human discussion and intent framing.
4. Agent internal reasoning.

### 3.5 Minimal Necessary Change
Keep diffs small, scoped, and validated. Avoid speculative architecture.

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

In practice, these evals should be repository-native (tests/scripts/config), versioned,
and required in the same run loop as functional tests.

## 5. Bootstrap Sequence
A practical sequence for new repositories:
1. Install baseline governance rules.
2. Define a reusable implementation agent.
3. Add domain skills (framework, API, language discipline).
4. Define one-pass task protocol.
5. Install baseline agent evals (outcome/process/policy/regression).
6. Consolidate planning docs.
7. Start task execution with strict validation, eval gating, and handoff logging.

## 6. Role of Friday in This Pattern
In this repository, Friday functions as the primary implementation operator under explicit constraints:
- Understand first, edit second.
- Prefer architectural analysis tools for exploration.
- Use code reads for concrete details only.
- Prefer native IDE tooling over shell-heavy text workflows.
- Stop and ask when tools are missing or choice is ambiguous.

Friday is not the governance source; governance remains in repository rules and operator decisions.

## 7. Benefits
### 7.1 Predictability
Runs become more consistent across time and across agents.

### 7.2 Auditability
Intent, constraints, and outcomes are documented and versioned.

### 7.3 Throughput With Lower Entropy
Less time is spent recovering from avoidable deviations.

### 7.4 Scalability
New repos can reuse the same bootstrap with minimal adaptation.

## 8. Risks and Mitigations
### Risk: Excess ceremony
Mitigation: keep kickoff protocol minimal and task-scoped.

### Risk: Over-constrained agents
Mitigation: allow clarification loops and explicit operator overrides.

### Risk: Stale instruction artifacts
Mitigation: treat agent and skill files as maintained code, reviewed during roadmap updates.

### Risk: False confidence from policy
Mitigation: enforce validation commands and report residual risks explicitly.

### Risk: Evals become brittle or noisy
Mitigation: start with a small stable eval set, add waivers with expiry/removal tickets,
and keep thresholds explicit and machine-readable.

### Risk: Goodhart pressure on a single metric
Mitigation: balance eval facets (outcome + process + policy + regression + stress)
instead of optimizing only one score.

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

## 10. Standardization Pattern
For cross-repo adoption, keep a small reusable package:
- Governance template.
- Primary implementation agent template.
- Core skills (framework, API, language discipline).
- Task protocol and decision-log template.
- Docs skeleton for design and implementation prep.

This enables a repeatable standard move: install AgentOps Bootstrap first, implement second.

Standardization should include a minimal eval starter pack:
- Machine-readable boundary config.
- At least one policy eval and one regression eval.
- Clear command contract to run evals locally and in CI.
- Waiver protocol with explicit rationale and removal task linkage.

## Conclusion
AgentOps Bootstrap reframes AI coding from assistant usage to operational engineering. By installing governance, role design, execution protocol, and eval planes directly in the repository, teams gain a durable system that improves reliability, safety, and delivery velocity without sacrificing operator control.

## Pony Farm
The "pony farm" pattern is how learning compounds across repos: each hard-won lesson becomes a portable, runnable artifact instead of a remembered preference.

One practical pony to raise first is an AgentOps eval starter for Python repositories:
- A machine-readable boundary policy file.
- A small boundary checker module.
- A gating test wired into the normal test run.
- A waiver protocol with explicit reason and removal ticket linkage.
- A short operator note with run command and target values.

This creates a repeatable transfer loop:
1. Learn from one repo.
2. Encode the lesson as policy plus checks.
3. Reuse the bundle in the next repo.
4. Tighten thresholds as architecture improves.

The result is durable progress: better defaults, lower variance, and less dependence on memory or prompt wording.
