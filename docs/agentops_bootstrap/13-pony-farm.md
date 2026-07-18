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

Pony Farm backlog (later thoughts and possible implementation order):
- Import boundary eval: enforce allowed layer dependency directions.
- Public API drift eval: detect accidental export contract changes.
- Forbidden pattern eval: block risky shortcuts (for example broad except, debug leftovers in runtime paths).
- Error-message quality eval: require actionable diagnostics for known failure modes.
- Config schema stability eval: detect breaking key changes without compatibility bridge.
- CLI contract eval: verify command/flag behavior and exit-code expectations.
- Documentation freshness eval: smoke-check command snippets used in docs.
- Waiver hygiene eval: require reason plus removal linkage and prevent waiver sprawl.
- Eval runtime budget eval: keep eval suite fast enough to run every cycle.
- Decision-log completeness eval: ensure task outcomes include validation and risk notes.
- Struggle-loop completeness eval: require detection, mechanism analysis, and guidance encoding when repeated friction appears.

[<- Previous: Conclusion](./12-conclusion.md) | [Index](./index.md)
