# ADR-0001: Adopt ADR Process for Technical Decisions

- Status: Accepted
- Date: 2026-04-11
- Jira: KAN-5
- PR: to be added

## Context

The project now tracks delivery work with Jira and links it to branches, commits, and pull requests.
Important technical decisions still risk being lost in chat, ticket comments, and review threads.

## Decision

Adopt a lightweight ADR process in-repo under `docs/adr`.
All significant technical and process decisions must be recorded as an ADR.

## Alternatives Considered

1. Keep decisions only in Jira comments and PR threads.
2. Keep decisions only in README files.
3. Use a separate external wiki for all decisions.

## Consequences

### Positive

- Better long-term traceability for "why" decisions were made.
- Faster onboarding and easier incident/root-cause investigations.
- Clear link between Jira issue, implementation PR, and decision rationale.

### Negative / Trade-offs

- Small documentation overhead for each significant decision.
- Requires discipline to keep ADR status and references current.

## Follow-up Actions

- [ ] Add PR link after merge.
- [ ] Create ADR-0002 for the next major technical decision.
