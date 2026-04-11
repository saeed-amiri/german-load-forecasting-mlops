# Incident Example: API 5xx Error Spike

## Title

[Incident] Forecast API returns elevated 5xx responses after deployment

## Detection

- Start time: 2026-04-10 08:15 UTC
- Detected by: Prometheus alert (5xx rate threshold exceeded)

## Customer Impact

- Who is affected: API consumers using forecast endpoint
- What is degraded or unavailable: increased request failures and delayed downstream analytics jobs

## Current Status

- Monitoring

## Timeline

1. Detection: alert fired for 5xx error-rate spike.
2. Mitigation start: traffic shifted to previous stable container image.
3. Recovery: 5xx rate returned below threshold.
4. Full resolution: root-cause investigation ticket created and tracked.

## Owner And Responders

- Incident owner: on-call platform engineer
- Responders: API engineer, data engineer

## Communication Plan

- Update cadence: every 30 minutes until resolved
- Stakeholder channel: #ops-alerts and incident thread in Jira

## Resolution Criteria

- API 5xx rate remains below agreed threshold for 60 minutes.
- No new customer-facing error reports for the incident window.

## Post-Incident Actions

- [ ] Root cause analysis ticket created
- [ ] Preventive action ticket(s) created
- [ ] PR linked to Jira issue(s)
