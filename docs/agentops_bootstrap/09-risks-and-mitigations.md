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

### Risk: Rigidity/flexibility imbalance
Mitigation: lock strategic invariants, but allow tactical adaptation under explicit verification and operator oversight.

### Risk: Failure aversion hides learning opportunities
Mitigation: require explicit error-to-learning capture in retros and decision logs.

[<- Previous: Benefits](./08-benefits.md) | [Index](./index.md) | [Next: Evaluation Metrics ->](./10-evaluation-metrics.md)
