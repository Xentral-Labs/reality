# Feature Specification: Reservations Keep Their Stored Status (Measured Decision)

**Feature Branch**: `317-reservation-resolutions`

**Created**: 2026-10-02

**Status**: Decided — not implemented

**Language**: English

**Input**: Owner request after spec 316: apply the stock-block shape (an unchanging record plus appended resolutions, open state derived at read time) to `reservation`. The owner agreed to measure first and decide on numbers.

## Context and Intent

### Problem

`reservation` stores a lifecycle `status` (`active`, `released`, `consumed`) and splits rows:

- A partial shipment marks the whole row `consumed` with its full quantity and continues the rest as a new `active` row. The consumed part is only in the `reservation.consumed` event payload (`consumed_quantity`). The link to the continuation row is only in the `reservation.created` event (`previous_reservation_id`).
- Releasing what a shipment from another location left beyond the open quantity does the same with `released`.
- A quantity revision of the promise releases every active reservation and creates new ones, so ids change.

Unlike `stock_block` before spec 316, the reserved quantity is never overwritten. `status` is not a copy of another stored truth either: it is the only record of what happened. It loses detail, but it is not a second authority.

### Scope

- Measure what deriving a reservation's open quantity costs on the hot read paths.
- Record the decision and its evidence so the question can be reopened against numbers.

### Non-Goals

- Any schema, service, adapter or analytics change to `reservation`.
- Changing spec 316 (`stock_block`), where the same shape is cheap because blocks are few.

## Clarifications

### Session 2026-10-02

- Q: Measure first or rebuild directly? → A: Measure first; rebuild only if the numbers are acceptable. (Owner.)
- Q: May the analytics graph lose `reservation.status`? → A: Yes, if the rebuild happens. (Owner; moot after the decision.)
- Q: The numbers are in; rebuild? → A: No. Record the measurement and keep the stored status. (Owner, 2026-10-02.)

## Evidence

See [research.md](research.md) for the method, the full table and how to rerun it. In short, on one company with 200,000 reservations (about a year at 550 orders a day):

- Targeted reads (one item at a location, 500 promises, the register page) can stay cheap with a per-row correlated sum: 4–25× the buffers of today, still milliseconds.
- Company-wide reads (reserved per item, per item and location) go from **105 buffers / ~2 ms** to **155,832 buffers / ~310–360 ms** at best. These feed the inventory register, the operational projections and the exception derivations that specs 180 and 235 made fast.
- The growth is inherent. "Open" is the stated quantity less a sum of later rows, which no index can hold, so every company-wide read scans the whole reservation history instead of the open reservations.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The decision can be reopened against numbers (Priority: P1)

As the owner, when the lean-tables question comes back for `reservation`, I find what was measured, how and why it was declined, and I can rerun the measurement on today's schema.

**Why this priority**: It is the whole deliverable.

**Independent Test**: The measurement script runs against a disposable database migrated to head, and its five reads return the same answers in both shapes.

**Acceptance Scenarios**:

1. **Given** this spec, **When** the script in `research/` is run as documented, **Then** it builds a disposable database, reports time and buffers for today's shape and both proposed variants, confirms equal answers, and drops the database.

### Edge Cases

- The script refuses nothing and touches no shared database: it creates and force-drops its own `reality_benchmark_317_*` database.
- Timings depend on host load; buffers do not, and the decision rests on buffers.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `reservation` MUST keep its stored `status` and its split behaviour unchanged.
- **FR-002**: The measurement MUST stay reproducible from `research/measure_open_reservations.py`.

### Domain and Architecture Requirements

- **DR-001**: A future proposal to derive reservation state MUST show company-wide reads in the same order of buffers as today, for example by deriving by change (spec 181 FR-002, spec 241), before the schema changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The decision and its numbers are recorded in this directory and linked from spec 316's non-goals.

## Assumptions and Dependencies

- The fixture's shape (2 % open, 3 % released, one in ten consumed reservations shipped in two parts) approximates a trading company; the conclusion does not depend on the exact mix, because the cost of the company-wide reads follows the total history.
- If the gap in truth ever matters (a reader that needs the consumed part per row), the smaller option is an appended history beside the stored status. That is an explicit exception to rule 11 and adds a table, so it was not taken.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | — | no code change in this feature |
| FR-002, SC-001 | US1 1 | `research/measure_open_reservations.py`, `research/results-2026-10-02.json` |
| DR-001 | — | this spec |
