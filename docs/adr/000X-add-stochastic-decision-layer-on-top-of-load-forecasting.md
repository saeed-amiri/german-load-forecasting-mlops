# ADR-000X: Add Stochastic Decision Layer on Top of Load Forecasting

- Status: Proposed
- Date: 2026-04-17
- Jira: TBD
- PR: TBD

## Context

Current forecasting pipeline is focused on point predictions from classical supervised models. That is useful for baseline accuracy, but does not fully support risk-aware operational decisions under uncertainty.

For grid-related use cases, point estimates alone are insufficient. We need a decision-oriented layer that can answer:

- What is the distribution of possible future load trajectories?
- What is the downside risk if the forecast is wrong?
- What action should be taken under uncertainty and risk constraints?

Given available infrastructure (training pipeline, config-driven orchestration, Airflow, and planned MLflow integration), a staged extension can be added without replacing existing models.

This ADR defines a future direction only. No implementation is required in this phase.

## Decision

Adopt a two-block extension beyond classical point forecasting:

1. Stochastic scenario generation (Monte Carlo)
- Train a baseline forecaster as currently done.
- Model residual process and temporal dependence.
- Generate many plausible future trajectories for forecast horizon.
- Treat these trajectories as uncertainty scenarios.

2. Risk-aware decision layer (stochastic optimization)
- Optimize decisions against generated scenarios.
- Use objective combining expected cost and tail risk, for example CVaR.
- Support probability (chance) constraints for reliability targets.

Reference objective form:

min_u E[C(u, xi)] + lambda * CVaR_alpha(C(u, xi))

Reference chance constraint form:

P(shortfall <= 0) >= 1 - epsilon

This creates a decision-grade workflow: forecast -> uncertainty -> action recommendation.

## Alternatives Considered

1. Keep only classical point forecasting
- Simple and low effort.
- Does not provide formal risk quantification for operations.

2. Add probabilistic intervals only (quantiles/conformal)
- Improves uncertainty reporting.
- Still does not directly optimize actions under risk preferences.

3. Add a full game-theoretic market layer first
- High analytical value.
- Too large as first step; should follow after scenario/risk foundation is stable.

## Consequences

### Positive

- Moves the project from prediction-only to decision under uncertainty.
- Adds clear theoretical depth (Monte Carlo, stochastic optimization, risk measures).
- Better alignment with operational planning and robustness requirements.
- Strong portfolio differentiation for advanced MLOps and quantitative methods.

### Negative / Trade-offs

- Higher implementation complexity and validation burden.
- More compute cost due to scenario simulation and optimization loops.
- Additional assumptions to maintain (residual model, risk aversion parameters, constraints).
- Requires careful observability for scenario quality and optimization stability.

## Follow-up Actions

- [ ] Define minimal scenario generator specification (residual model, horizon, number of scenarios).
- [ ] Define risk metric contract (VaR/CVaR, coverage, calibration checks).
- [ ] Define decision API contract for recommendation output and diagnostics.
- [ ] Add config schema draft for stochastic settings (without enabling in production path).
- [ ] Plan phased rollout: simulation report mode -> offline optimization -> optional online use.
- [ ] Create a separate implementation ADR if/when coding starts.
