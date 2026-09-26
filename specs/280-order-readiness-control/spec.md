# Feature Specification: Order Readiness Control

**Feature Branch**: `280-order-readiness-control`
**Created**: 2026-09-26
**Status**: Approved scope
**Language**: English
**Input**: Give operators and agents one explainable Sales readiness view for future-dated, partially stocked, prepayment-blocked and ready customer orders, including visible projection freshness and traceable blockers.

## Context and Intent

### Problem

The Sales customer-order register currently shows received document evidence: order number,
customer, date, amount, line count and source. It does not show whether an order can ship, what
quantity is reserved or missing, whether prepayment blocks dispatch, or whether the displayed
operational answer is current. Operators must ask Chat or traverse each commitment separately.

Reality already derives the canonical fulfillment queue from Commitments, Reservations, Movements,
holds and payment evidence. The missing product slice is to present that shared result as a bounded
operational control surface without copying readiness onto Documents or recalculating it in the
browser.

### Scope

- Add a Sales readiness view backed only by the canonical fulfillment queue projection.
- Show customer order, customer, requested/due date, readiness, line quantities, reservation,
  shortage, payment gate and blocker reasons in scan-friendly business language.
- Distinguish fully ready, partly covered, blocked and closed work without inventing a stored order
  status.
- Show projection observation time and pending-change metadata; stale or unavailable state must not
  be presented as current truth.
- Link each order and line to the existing Document, Commitment and Inspector explanations.
- Keep the existing customer-order evidence register unchanged as the agreement/source view.

### Non-Goals

- No automatic reservation, shipment, invoice, payment or allocation.
- No new delivery, payment or readiness fields on Documents.
- No new calculation in React and no second fulfillment rule.
- No projection refresh from a GET request or browser timer.
- No new partial-shipment policy; the view reports existing canonical readiness and line coverage.
- No replacement of the Warehouse queue, fulfillment blockers report or Chat explanation.

### Existing Contracts

- `.specify/memory/constitution.md`.
- `docs/WEB_SPEC.md` and `docs/WEB_UX_MATRIX.md` Orders/Warehouse Queue contracts.
- `docs/features/order_to_cash.md`, `docs/features/shipments.md` and
  `docs/features/home-live-status.md`.
- `specs/113-orders-deliveries/spec.md`.
- `specs/275-fulfillment-safety-parity/spec.md`.

## User Scenarios & Testing

### User Story 1 - Scan what can ship and why (Priority: P1)

A Head of Operations opens Sales readiness and immediately sees which customer orders are ready,
blocked by stock or reservation, blocked by prepayment, or no longer active. Multiple customers and
future requested dates can be compared without opening each record.

**Why this priority**: The current evidence register cannot answer the daily operational question
of what can ship and what needs intervention.

**Independent Test**: Seed ready, stock-short, reservation-short and unpaid-prepayment orders for
different customers and assert that one bounded page shows the canonical decision and exact blocker
codes/amounts for each.

**Acceptance Scenarios**:

1. **Given** a fully reserved, stocked order without a payment blocker, **When** readiness is opened,
   **Then** the order is labelled ready and its open/reserved/shortage quantities reconcile.
2. **Given** an order with only part of its open quantity reserved or stocked, **When** the row is
   read, **Then** it is blocked and shows the exact uncovered quantity and blocker reasons.
3. **Given** a prepayment order with sufficient stock but insufficient qualifying allocation,
   **When** readiness is opened, **Then** it shows required, received and remaining money and names
   prepayment as the blocker.
4. **Given** multiple lines with different blockers, **When** the order is shown, **Then** the
   summary includes the complete blocker set and line detail retains each line's quantities.

---

### User Story 2 - Know whether the answer is current (Priority: P1)

An operator can see when the readiness projection was observed and whether newer company events are
pending. A missing or stale snapshot is explicit and never represented as a fresh ready decision.

**Why this priority**: Agents and people cannot safely act on a readiness answer while newer stock,
payment or reservation changes are not reflected.

**Independent Test**: Read a completed snapshot, append a relevant event without refreshing, and
verify the previous rows remain visible but are clearly marked with pending-change range/count; read
an unavailable snapshot and verify a non-authoritative unavailable state.

**Acceptance Scenarios**:

1. **Given** a completed current snapshot, **When** the page loads, **Then** it shows the observation
   time and no pending-change warning.
2. **Given** newer relevant events after the snapshot, **When** the page loads, **Then** it retains
   the last completed rows, dims or warns them, and states the pending event range/count.
3. **Given** no completed fulfillment snapshot, **When** readiness is opened, **Then** the page
   explains that readiness is unavailable and does not show zero or ready as a substitute.
4. **Given** a read failure, **When** the page remains open, **Then** it retains the shared error and
   retry behavior without triggering refresh work.

---

### User Story 3 - Trace and continue from the blocker (Priority: P2)

An operator expands an order, inspects its line commitments and follows the existing explanation to
the underlying Reservation, Movement, Ledger allocation, evidence and Source. Available actions use
the existing reviewed application tools.

**Why this priority**: A readiness badge without an explanation path cannot give agents or operators
full control over the current business state.

**Independent Test**: Expand stock- and payment-blocked rows and verify exact opaque links open the
existing Commitment/Document inspectors and preserve the path to evidence and source.

**Acceptance Scenarios**:

1. **Given** a readiness row, **When** its order is inspected, **Then** the exact Document opens and
   exposes existing Evidence and Source links.
2. **Given** a blocked line, **When** its line detail is inspected, **Then** the exact Commitment
   opens with current reservation, movement, hold and payment explanation.
3. **Given** an available mutation, **When** an operator chooses it, **Then** the existing proposal
   and human confirmation flow is used; the readiness page performs no direct write.

### Edge Cases

- An order has no active customer-delivery commitment: it is absent from active readiness or appears
  closed according to the canonical projection; the browser does not infer a reason.
- Quantities in different units remain separate by line and are never summed across units.
- A source-stated requested date is absent: the view shows no requested date, not a calculated one.
- A net-term order may be unpaid and still ready when no other blocker exists.
- A prepayment invoice is missing or attribution is ambiguous: canonical specific blocker reasons
  are shown instead of a generic unpaid label.
- Pending changes are interpreted only by the shared projection metadata contract.
- Search and pagination apply server-side before the bounded response.

## Requirements

### Functional Requirements

- **FR-001**: Sales MUST expose a distinct customer-order readiness view alongside, not replacing,
  the existing customer-order evidence register.
- **FR-002**: The view MUST consume the canonical tenant-scoped fulfillment queue projection and
  MUST NOT calculate readiness, shortages or payment state in the browser.
- **FR-003**: Each order row MUST show customer, order reference, due/requested date, readiness,
  complete blocker reasons and a concise quantity summary.
- **FR-004**: Expanded line detail MUST show item, unit, open, fulfilled, reserved and shortage
  quantities without summing incompatible units.
- **FR-005**: Prepayment lines MUST show the canonical required, qualifying received and remaining
  amounts when present; net-term unpaid orders MUST NOT be labelled payment-blocked.
- **FR-006**: Ready, blocked and closed labels MUST be derived solely from the projection result and
  use restrained localized business language.
- **FR-007**: The response and page MUST expose the completed snapshot observation time and canonical
  pending-change metadata.
- **FR-008**: Pending changes MUST keep the last completed answer visible while clearly marking it as
  not current; the browser MUST NOT trigger projection maintenance from the read path.
- **FR-009**: Missing projection data MUST produce an explicit unavailable state, not an empty-ready
  or zero-valued operational answer.
- **FR-010**: Search and pagination MUST remain bounded and server-side with tenant isolation.
- **FR-011**: Order rows MUST link to the exact Document and line rows to exact Commitments through
  existing Inspector routes.
- **FR-012**: Any mutation launched from the readiness context MUST use existing shared proposal and
  explicit human confirmation flows.
- **FR-013**: New user-facing text MUST be complete in English, German, Dutch and Spanish.
- **FR-014**: Browser acceptance MUST cover 390px and 1440px layouts, keyboard-operable expansion,
  loading, unavailable, stale, error and current states.
- **FR-015**: Chat and external MCP reads MUST retain the same fulfillment queue and readiness
  results; this feature MUST NOT introduce a Web-only business interpretation.

### Domain and Traceability Requirements

- **DR-001**: Readiness remains a materialized observation from Commitment, Reservation, Movement,
  hold and Ledger allocation records; it is never stored as Document authority.
- **DR-002**: Document → DocumentLine → Commitment remains the shortest evidence-to-reality path;
  Reservation and Movement links remain attached to Commitment.
- **DR-003**: All reads remain tenant-scoped and use the shared projection/application services.
- **DR-004**: Exact source-stated dates and amounts are displayed as received; derived coverage and
  remaining amounts are explicitly presented as observations.

### Key Entities

- **Order Readiness Row**: A projected operational summary for one order with active line commitments
  and blocker aggregation.
- **Readiness Line**: One commitment-level quantity and blocker explanation retaining its unit.
- **Projection Metadata**: Observation time, covered event sequence and pending changes.
- **Document and Commitment links**: Opaque identities for existing Inspector traversal.

## Success Criteria

- **SC-001**: In the acceptance dataset, 100% of ready, stock-short, reservation-short and unpaid-
  prepayment orders match the canonical fulfillment queue decision and blocker set.
- **SC-002**: Every displayed order and line quantity reconciles exactly to the projection payload;
  no cross-unit sum is displayed.
- **SC-003**: Every tested stale snapshot shows pending-change metadata, and zero stale snapshots are
  presented without a warning.
- **SC-004**: Every tested missing snapshot produces an unavailable state and no fabricated zero or
  ready value.
- **SC-005**: Every order/line tested reaches the correct Document/Commitment Inspector and onward
  Evidence/Source trace.
- **SC-006**: Backend projection/API, four-language UI, responsive browser and existing Chat/MCP
  parity tests pass.
- **SC-007**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Existing fulfillment queue projection and metadata are authoritative and tenant-scoped.
- Spec 275 remains authoritative for payment and dispatch readiness calculations.
- Projection maintenance belongs to the scheduler/worker; this feature only reads the latest snapshot.
- No schema or migration is required.
- Existing Document and Commitment inspectors provide trace continuation.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-006 | US1 | Projection/API contract and readiness table tests |
| FR-007–FR-010 | US2 | Current/stale/missing/error metadata tests |
| FR-011–FR-012 | US3 | Inspector routing and reviewed-action regression |
| FR-013–FR-014 | US1–US3 | i18n audit and responsive browser contract |
| FR-015 | US1–US3 | Web/Chat/MCP normalized projection parity |
| DR-001–DR-004 | US1–US3 | Domain trace, tenant and value-authority assertions |
