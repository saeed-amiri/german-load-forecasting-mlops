# 0003-Epic-Gateway-UI-and-Portal-Integration

- Status: Accepted
- Date: 2026-05-08
- Jira: KAN-28 (https://saeed-amiri.atlassian.net/browse/KAN-28)
- PR:

**Update this ADR only in the this branch: KAN-28-gateway-ui-portal-integration**

## Context

The current platform has training and MLOps foundations in place (ADR-0002), and now requires a user-facing integration layer.

This epic defines the sequence for connecting Gateway UI, Dashboard, Auth, and Portal with clear role boundaries.

## Decision

Implement Gateway UI and Portal integration in the following order:

1. Close previous epic pending items and prepare baseline
- Review open TODOs from ADR-0002 and close blockers that can break UI/Portal integration.
- Freeze baseline contracts (config keys, service names, auth endpoints).
- Outcome: stable base for integration work.

2. Add Dashboard entrypoint in Gateway UI
- Add a clear Dashboard link/route in Gateway UI navigation.
- Ensure route works in local and docker-compose environments.
- Outcome: users can reach the new frontend surface from Gateway.

3. Update UI information architecture and visual modules
- Implement required tabs and graph views.
- Align data widgets with expected portal payload contracts.
- Outcome: UI shell is ready to consume real portal data.

4. Integrate Auth service and enforce RBAC
- Connect UI login/session flow to Auth service.
- Define and apply role matrix:
    - Admin: full visibility + user/permission management.
    - User: own-scope visibility only, no user/permission management.
- Enforce RBAC in both UI guards and API authorization checks.
- Log all access attempts for auditing and debugging.
- Outcome: consistent access control across frontend and backend.

5. Integrate UI with Portal APIs
- Implement/adjust portal endpoints required by UI graphs and tabs.
- Add robust error handling for empty, delayed, or unavailable data.
- Validate end-to-end data flow from Portal to UI components.
- Outcome: UI reads live portal data through supported APIs.

6. Apply configuration permission policy
- Ensure all users have read-only access to allowed config views.
- Ensure admins have read-write access where management is required.
- Audit config surfaces in UI and API for permission consistency.
- Outcome: config access matches role policy (User: RO, Admin: RW).

## Implementation Checklist (Execution Order)

- [ ] Step 1 complete: previous epic TODOs reviewed/closed and baseline frozen.
- [ ] Step 2 complete: Dashboard link is available and reachable.
- [ ] Step 3 complete: tabs/graphs implemented with stable UI contracts.
- [ ] Step 4 complete: Auth integration + RBAC enforced in UI and API.
- [ ] Step 5 complete: Portal endpoints integrated and validated end-to-end.
- [ ] Step 6 complete: config RO/RW permissions verified by role.

## Consequences

### Positive
- Creates a clear delivery order for cross-service integration.
- Reduces rework by introducing access control before final API hardening.
- Improves maintainability by validating role policy in both UI and API layers.

### Negative / Trade-offs
- Requires coordination across Gateway UI, Auth, and Portal teams.
- Adds dependency on RBAC correctness before broader rollout.
- May increase delivery time due to end-to-end integration validation.

## Follow-up Actions

- [ ] Link each step to a dedicated Jira sub-task under KAN-28.
- [ ] Add integration tests for role-based API access and UI route guards.
- [ ] Add smoke tests for Dashboard route and Portal data rendering.
