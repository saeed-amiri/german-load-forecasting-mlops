# ADR-000Y: Add Model A/B Testing Layer for Forecasting Policies

- Status: Proposed
- Date: 2026-04-17
- Jira: TBD
- PR: TBD

## Context

The current project supports configurable model training and inference, but does not yet provide a formal mechanism to compare candidate models or decision policies under controlled experimentation.

A/B testing appears frequently in ML and data roles, but for this project the relevant interpretation is policy/model experimentation rather than UI experimentation.

For load forecasting, a useful A/B framework should:

- Compare baseline policy (A) against candidate policy/model (B).
- Use operational metrics (error and risk/cost proxies), not only generic uplift.
- Start safely in offline replay mode before any live routing split.

This ADR defines a future architecture direction only. No implementation is required in this phase.

## Decision

Introduce a lightweight experimentation layer for model/policy A/B testing with staged rollout:

1. Offline replay A/B as the default first phase.
- Replay historical windows.
- Compute per-window metrics for A and B.
- Estimate effect sizes and confidence intervals.

2. Optional online shadow/canary phase later.
- Route a small percentage of requests to candidate policy B.
- Log assignment and outcomes for statistical comparison.

3. Promotion rule based on guardrails.
- B is promotable only when primary metric improves and no guardrail metric regresses beyond threshold.

## Alternatives Considered

1. No A/B layer; rely on ad hoc model comparisons.
- Lower effort.
- Harder to justify model changes with reproducible evidence.

2. Immediate online traffic split without offline replay.
- Faster signal collection.
- Higher operational risk and weaker initial reliability.

3. Full multi-armed bandit from start.
- Potentially efficient exploration.
- Added complexity before baseline A/B governance is mature.

## Consequences

### Positive

- Adds a standard experimentation capability expected in production ML workflows.
- Improves decision quality for model promotion with explicit evidence.
- Supports both statistical rigor and operational guardrails.
- Integrates naturally with planned MLflow tracking and Airflow orchestration.

### Negative / Trade-offs

- Additional metrics and reporting complexity.
- Requires careful experiment design (sample size, leakage prevention, horizon alignment).
- Can delay model releases if governance thresholds are strict.

## Follow-up Actions

- [ ] Define minimal experiment config contract (variant A, variant B, split ratio, sample size, guardrails).
- [ ] Define offline replay evaluation protocol and data slicing rules.
- [ ] Define statistical report outputs (delta, CI, p-value, practical significance).
- [ ] Define promotion policy and rollback criteria.
- [ ] Add implementation ADR if coding starts.
