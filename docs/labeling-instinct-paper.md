# Labeling Instinct: Turning Golden-Path Intuition into a Transferable Software Method

## Abstract
Some engineers repeatedly find the best development line under uncertainty. Their decisions look intuitive, but the intuition is often compressed expertise: pattern recognition plus fast forcing-line evaluation. This paper introduces a lightweight method to externalize that skill without killing it through over-process. The method captures only high-leverage decision moments, labels the earliest predictive signals, and builds a reusable library of decision patterns.

## 1. Problem Statement
Many strong software decisions are made in milliseconds and explained in minutes. Teams see the answer but not the mechanism. The result is dependency on one person, repeated overreach by others, and inconsistent quality under ambiguity.

Typical failure modes:
- Over-generalization: adding plausible but unrequested semantics.
- Speculative structure: designing for imagined futures.
- Ambiguity drift: choosing branches without explicit operator resolution.
- Post-hoc rationalization: writing polished explanations that hide the actual trigger signal.

The central challenge is not intelligence. It is extraction. How can intuition be labeled and transferred while preserving speed and quality?

## 2. Core Thesis
Intuition can be made teachable by labeling decision points, not by documenting everything.

The right unit of capture is a fork in the road:
- What was the position?
- What candidate moves existed?
- Which signals killed weak branches?
- Why was one line most forcing?

This preserves the cognition that matters and discards narrative noise.

## 3. Concept Model
The model has three layers:
- Pattern recognition layer: identify familiar problem shape quickly.
- Forcing-line layer: evaluate branch consequences and reversibility.
- Constraint layer: enforce scope, type, and contract truth.

The skill emerges when these layers align under pressure.

## 4. Method: The 5-Line Decision Capture
Capture only moments that changed direction. Use this exact format:

1. Context
- What problem shape was present?

2. Candidate paths
- What were the 2 to 4 plausible moves?

3. Kill criteria
- What made non-winning paths wrong?

4. Golden path
- Which line was chosen and why was it most forcing?

5. Earliest signal
- What was the first clue that predicted this outcome?

Completion rule:
- If this takes longer than 2 minutes, it is too heavy and should be simplified.

## 5. Ambiguity Discipline
Treat ambiguity as branching risk, not creativity space.

Operational rule:
- If two or more interpretations remain valid, ask one focused question and stop branch execution until answered.

This preserves decision quality and blocks speculative drift.

## 6. Pattern Library Design
Store captures in a compact library organized by shape, not by project.

Recommended fields per entry:
- Shape name
- Trigger signal
- Common trap
- Winning line
- Boundary condition
- Counterexample

Example shape names:
- Premature grammar trap
- Config surface inflation
- Abstraction before invariants
- Validation semantics leak
- Compatibility theater

## 7. Quality Filters
A good capture is:
- Specific: tied to an actual branch decision.
- Falsifiable: includes a counterexample or boundary condition.
- Compressed: minimal words, maximal signal.
- Transferable: useful outside the original task.

A bad capture is:
- Broad advice without branch context.
- Moral framing instead of decision mechanics.
- Retrospective storytelling with no trigger signal.

## 8. Worked Example (Scheduling Contract)
Context:
- Contract field for schedule and deadline under underspecified behavior.

Candidate paths:
- A: Structured schedule object with grammar discriminator.
- B: Minimal scalar schedule with deferred strategy semantics.
- C: Add timezone and natural-language deadline interpretation.

Kill criteria:
- A introduces unrequested policy grammar.
- C introduces semantics not present in type contract.

Golden path:
- B. Keep schedule as opaque string and deadline as concrete datetime type.

Earliest signal:
- Requirement emphasized simple scheduling and warned against implementation traps.

## 9. Adoption Plan (Low Ceremony)
Week 1:
- Capture 3 to 5 decision forks only.

Week 2 to 4:
- Label repeated signal patterns.
- Merge duplicates.

Month 2:
- Produce a one-page index of top 10 shapes.
- Use index during design reviews.

Do not do:
- Full logs.
- Mandatory capture for every task.
- Complex taxonomy before enough examples exist.

## 10. Evaluation Metrics
Track a small set:
- Branch reversal rate: how often chosen path is later undone.
- Speculation incidence: number of unrequested semantics introduced.
- Clarification latency: time from ambiguity detection to operator answer.
- Reuse count: how often a prior shape was used to make a new decision.

Success signal:
- Fewer branch reversals and less speculative churn with no increase in delivery friction.

## 11. Anti-Patterns
- Process inflation disguised as rigor.
- Capturing outcomes without signal triggers.
- Turning the library into compliance paperwork.
- Treating intuition as magic instead of compressed evidence.

## 12. Closing
Golden-path intuition is not a mysterious gift that cannot be shared. It is a high-speed, high-discipline selection process that can be labeled at decision forks. Capture less, but capture the right thing. Over time, a compact pattern library turns private instinct into team capability.

## Appendix A: Blank Decision Card
- Shape name:
- Context:
- Candidates:
- Kill criteria:
- Golden path:
- Earliest signal:
- Boundary condition:
- Counterexample:

## Appendix B: 60-Second Review Prompt
- Did we choose a line or a story?
- Which branch was eliminated first and why?
- What assumption would break this line?
- What single question would have prevented the biggest risk?
