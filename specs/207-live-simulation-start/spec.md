# Feature Specification: Live simulation start and header

**Feature Branch**: `207-live-simulation-start`
**Created**: 2026-09-15
**Status**: Implemented and locally verified
**Language**: English
**Input**: Start the first live demo orders sooner and show a subtly pulsing header link only while live simulation is running.

## Context and Intent

### Problem

New companies wait a full interval and possibly several empty random deliveries before their first live order. People cannot see the simulation's state while working elsewhere.

### Scope

- Three guaranteed initial orders on a fresh simulation start: immediately, at 12 seconds and at 24 seconds, followed by the selected normal rate.
- A compact Live simulation link in the top-right header, leading to the current company's Demo Data overview.

### Non-Goals

- No faster invoice/payment settlement, new business effects, new database tables, external integrations or scheduler processes.
- No startup replay for existing running simulations, ordinary resume or rate changes.
- No expansion of Demo Data access permissions or infrastructure health claims.

### Existing Contracts

- [Company setup/demo](../../docs/features/company-setup-demo.md), [scheduling](../../docs/features/scheduled-jobs.md), [Home live status](../../docs/features/home-live-status.md), [Web](../../docs/WEB_SPEC.md).

## User Scenarios & Testing

### User Story 1 - See initial activity promptly (Priority: P1)

A person creates a live demo company or explicitly starts a stopped simulation and sees its first orders without waiting for the normal stochastic delivery cadence.

**Why this priority**: Visible activity makes the live demo understandable.
**Independent Test**: Advance the shared scheduling clock through a fresh start and execute the ordinary intake jobs.

**Acceptance Scenarios**:

1. **Given** a confirmed fresh start and healthy workers, **when** initialization completes, **then** one order is due immediately and one each at 12 and 24 seconds, even when normal random demand would be zero.
2. **Given** the initial sequence completed, **when** more work is due, **then** the chosen normal rate and random demand apply.
3. **Given** retry, replay, pause, resume, rate change or downtime, **when** processing continues, **then** no duplicate or missed-interval burst occurs; pause/resume and rate changes end any remaining initial sequence.

### User Story 2 - Recognize and open live simulation (Priority: P1)

A person sees a subtle live indicator in the header and opens its existing overview directly.

**Why this priority**: Simulation controls should remain discoverable across the app.
**Independent Test**: Browser fixtures exercise status changes and company switching.

**Acceptance Scenarios**:

1. **Given** an authorized company with running simulation, **when** its status is read, **then** a compact subtly pulsing Live simulation link appears at the top right; activating it opens that company's Demo Data page.
2. **Given** no connection, paused, stopped, disconnected, throttled, failed or unavailable status, **when** the header renders or refreshes, **then** there is no live indicator.
3. **Given** a company switch or late response, **when** the selected company changes, **then** the previous company's indicator cannot appear.
4. **Given** reduced-motion preference or a narrow viewport, **when** simulation is running, **then** the link stays accessible; reduced motion disables its pulse.

### Edge Cases

- A stopped worker cannot guarantee wall-clock arrival: work remains durable and bounded.
- Delayed startup occurrences coalesce; no catch-up sequence after downtime.
- Failed status reads hide the positive indication; hidden tabs do not poll.
- Existing admission, owner eligibility and source controls remain authoritative.

## Requirements

### Functional Requirements

- **FR-001**: Fresh confirmed simulation starts MUST make one order due at 0, 12 and 24 seconds after activation, then use normal cadence. This includes automatic start after confirmed company initialization.
- **FR-002**: Startup MUST retain retry identity, queue limits, tenant isolation, source authorization, pause/stop and no catch-up burst semantics; resume/rate change MUST not restart it.
- **FR-003**: The header MUST show a compact Live simulation link only for the selected company's successfully read running, non-error simulation state, within ten seconds of a status change while visible.
- **FR-004**: The link MUST open the selected company's existing Demo Data overview without a mutation.
- **FR-005**: The indicator MUST have a subtle pulse, a localized accessible name, keyboard activation, responsive placement and no animation under reduced-motion preference.
- **FR-006**: Company switches, failed/timed-out reads and unauthorized access MUST never retain a positive indicator from an old observation. Reads MUST be bounded, non-overlapping and suspended while hidden.

### Domain and Traceability Requirements

- **DR-001**: All initial orders MUST use normal immutable SourceRecord → Document/DocumentLine → Commitment intake; no direct operational writes or new document status.
- **DR-002**: Initial timing MUST remain in the shared scheduler/queue; no browser production timer or separate queue. No new business schema is required.
- **DR-003**: The header MUST use existing tenant-scoped Demo Data service reads and permissions; no inference from the company name or a historical bootstrap flag.

### Key Entities

- Existing Demo Data connection, schedule, durable job run and source records; no new business entity.

## Success Criteria

- **SC-001**: A healthy idle local stack can process the first order on its next scheduler/worker sweep; three initial orders become eligible within 24 seconds of activation.
- **SC-002**: Browser acceptance proves correct visibility, tenant-safe navigation, state transitions, mobile layout and reduced motion.
- **SC-003**: Every FR and DR maps to executable proof before completion.

## Assumptions and Dependencies

- User accepted the proposed fast first order and short initial sequence, and explicitly requested the conditional header link. This records that accepted product scope; no additional scope approval is needed.
- Timings are eligibility targets, not a promise when infrastructure is delayed. Normal demand remains stochastic.
- Demo Data access currently requires eligible Sandbox ownership; this feature preserves that boundary.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-001, DR-001 | US1.1–2 | PostgreSQL startup intake tests |
| FR-002, DR-002 | US1.3 | shared scheduler startup/replay/control tests |
| FR-003–006, DR-003 | US2.1–4 | live-simulation-header browser acceptance |
