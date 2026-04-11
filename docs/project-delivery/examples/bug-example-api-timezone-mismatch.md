# Bug Example: API Timezone Mismatch

## Title

[Bug] Forecast timestamps returned in local time instead of UTC

## Severity

- High

## Environment

- Production
- Service or component: API inference endpoint
- Version or commit: main (latest deployment)

## Steps To Reproduce

1. Call the forecast endpoint for a known date range.
2. Compare returned timestamps with UTC reference timestamps.
3. Observe response payload uses local timezone offset.

## Expected Result

- Timestamps are returned in UTC with a consistent format expected by downstream dashboards and jobs.

## Actual Result

- Timestamps are returned with local timezone offset, causing alignment errors in monitoring and reporting.

## Evidence

- Logs: response serialization indicates local timezone conversion path.
- Screenshot: dashboard panel shifted by one hour.
- Error snippet: downstream validation fails on timestamp contract check.

## Suspected Cause

- Datetime serialization in API response path applies local timezone conversion before JSON encoding.

## Fix Validation

- [ ] Reproduction no longer fails
- [ ] Regression checks passed
- [ ] PR linked to Jira issue
