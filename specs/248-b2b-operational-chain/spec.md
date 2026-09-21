# Feature Specification: Explainable B2B Operational Chain

**Feature Branch**: `[248-b2b-operational-chain]`
**Created**: 2026-09-21
**Status**: Draft
**Language**: English
**Input**: "Close the gaps found while operating an empty company through a realistic B2B order-to-cash, procure-to-pay and returns cycle: retain invoice lines, expose contribution values, distinguish customer-specific supply from stock replenishment, guide return disposition and ensure every movement is explained."

## Context and Intent

### Problem

A company created empty can record orders, commitments, stock movements, invoice headers and
payments, but the ordinary operating path does not yet preserve one complete chain from an order
line through delivery, invoice line, retained acquisition cost and contribution. A realistic B2B
trial therefore reaches a contradictory result: stock and open items are visible, while DB1 and DB2
are unavailable because the invoice has no lines or the revenue line is not a supported contribution
scope.

The same trial exposes three adjacent control gaps. Incoming supplier supply cannot state whether it
was procured for a particular customer demand or for general stock. An arrived customer return does
not lead the operator through an explicit disposition decision. A movement can remain without a
business reason or source relationship even when the surrounding scenario knows why it happened.
These gaps prevent an operations or finance leader from explaining the full business result and make
an autonomous agent unsafe: it can see fragments but cannot reliably identify which demand supply
serves, what happened to returned goods, or which evidence supports margin.

### Scope

- Preserve normal sales and supplier invoice lines and their shortest true relationships when a
  business process creates invoices from existing operational evidence.
- Make supported invoiced B2B sales immediately readable as revenue, consumed retained acquisition
  cost, DB1, reviewed selling costs and DB2, with explicit unavailable reasons when evidence is
  incomplete.
- Let an operator state whether an incoming supplier quantity serves one or more customer delivery
  commitments or replenishes stock, and show the remaining unassigned supply without inferring a
  relationship.
- Guide an arrived customer return into an explicit disposition: restock, quarantine/repair,
  scrap/loss, or return to supplier, while retaining partial and unresolved quantities.
- Require movements created by the covered workflows and shipped examples to carry the shortest
  available explanation through a commitment, return announcement, correction, source evidence or
  explicit adjustment reason.
- Provide one executable multi-day B2B business story that begins with an empty company and proves
  order-to-cash, customer-specific procurement, stock replenishment, procure-to-pay, cancellation,
  return, credit and contribution outcomes.

### Non-Goals

- Automatic purchase-order generation, reorder-point planning, demand forecasting or supplier
  selection.
- Owning an upstream system's invoice totals, tax calculation, prices, costs or document numbering.
- Warehouse execution features such as pick routes, carrier booking, bin optimization or barcode
  hardware.
- Automated customer communication, RMA labels, supplier emails, refunds or bank transfers.
- Manufacturing, bills of material, project costing, landed-cost allocation or multi-entity
  consolidation.
- Silently manufacturing invoice lines, cost values, supply allocations or return decisions when
  the source or operator did not state them.
- Replacing the broad canonical demo catalog; the new story is focused acceptance evidence for the
  ordinary empty-company path.

### Existing Contracts

- [Business Reality Constitution](../../.specify/memory/constitution.md)
- [Web UI specification](../../docs/WEB_SPEC.md)
- [Data model](../../docs/DATA_MODEL.md)
- [Company setup and demo](../../docs/features/company-setup-demo.md)
- [Demo data catalog](../../docs/features/demo-data-catalog.md)
- [Inventory cost and contribution specification](../242-inventory-cost-contribution/spec.md)
- [Demo business journeys specification](../246-demo-business-journeys/spec.md)
- [Commercial edge workflows specification](../247-commercial-edge-workflows/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Invoice a Delivered B2B Sale With Contribution (Priority: P1)

An operations or finance user turns delivered customer order lines into a customer invoice. The
invoice retains the stated lines and links each line to the operational evidence it bills. Reality
then shows the received revenue, the exact retained cost consumed by the delivered quantity, DB1,
reviewed selling costs and DB2. Each amount can be traced back through Reality and Evidence to the
source that stated it.

**Why this priority**: A sale without invoice lines or contribution is not a complete commercial
result. It blocks the user's primary requirement and prevents reliable finance demonstrations.

**Independent Test**: In an otherwise empty company, receive valued stock, record and fulfil one
customer order, invoice the delivered quantity and inspect the invoice line. The invoice line shows
stated revenue and calculated DB1; after reviewed selling costs are added it also shows DB2, with
links to the consumed inventory basis and source evidence.

**Acceptance Scenarios**:

1. **Given** a fulfilled customer commitment with stated order-line price and sufficient retained
   acquisition cost, **When** the user invoices the delivered quantity, **Then** the invoice has one
   corresponding line linked through the shortest true operational relationship and shows received
   revenue, consumed acquisition cost and DB1.
2. **Given** reviewed selling costs for that invoice line, **When** the user opens its contribution
   explanation, **Then** DB2 equals DB1 less those reviewed costs and every component names its
   retained evidence.
3. **Given** a partial delivery, **When** only the delivered quantity is invoiced, **Then** revenue
   and consumed cost cover only that quantity and the uninvoiced remainder stays visible without
   being treated as revenue.
4. **Given** an invoice line whose cost or revenue basis is absent, stale or not reviewed, **When**
   contribution is read, **Then** the result is unavailable rather than zero and names the exact
   missing basis and next review action.
5. **Given** a source states invoice lines and totals, **When** the invoice is retained, **Then**
   Reality records those values without recomputing or silently balancing them; any disagreement is
   exposed separately.

---

### User Story 2 - Distinguish Customer Supply From Stock Replenishment (Priority: P2)

A purchaser records supplier supply and explicitly states whether a quantity is intended for a
named customer delivery commitment or for general stock. Operations can see the planned relationship,
received quantity, remaining supplier quantity and any customer shortage without confusing a plan
with a physical reservation or receipt.

**Why this priority**: B2B operators must answer whether supply protects a customer promise. Item-
level incoming quantity alone cannot answer that question safely.

**Independent Test**: Create two supplier commitments for the same item: one pegged to a customer
commitment and one marked as stock replenishment. Partially receive each and verify that the customer
view, purchasing view and inventory view agree on assigned, unassigned, received and outstanding
quantities.

**Acceptance Scenarios**:

1. **Given** an open customer delivery commitment and a supplier commitment for the same item,
   **When** the purchaser assigns part of the incoming quantity to that demand, **Then** both sides
   show the stated relationship and quantity without creating a reservation or movement.
2. **Given** a supplier commitment explicitly intended for stock, **When** it is viewed, **Then** it
   is labelled as stock replenishment and is not presented as protecting a customer promise.
3. **Given** one supplier quantity is split across two customer commitments and stock, **When** the
   allocation is inspected, **Then** assigned and remaining quantities reconcile exactly to the
   supplier commitment quantity.
4. **Given** a partial receipt, cancellation or supplier short shipment, **When** supply coverage is
   recalculated, **Then** physical receipt, open supplier quantity and stated demand assignment remain
   separate and shortages remain visible.
5. **Given** mismatched tenant, item, location or quantities above the remaining supplier/customer
   scope, **When** assignment is attempted, **Then** it is refused without disclosing or changing
   foreign-company data.

---

### User Story 3 - Resolve an Arrived Customer Return (Priority: P2)

A customer-service or warehouse user follows an announced return from arrival to an explicit
quantity-based disposition. Returned goods may be restocked, quarantined for inspection or repair,
scrapped as loss, or sent back to a supplier. Finance can separately issue and allocate the customer
credit; goods and money never imply one another.

**Why this priority**: Arrival alone does not say whether returned stock is sellable or financially
credited. Leaving that decision implicit overstates stock and hides unresolved customer work.

**Independent Test**: Announce and receive a five-unit customer return, restock two, quarantine one,
scrap one and send one to the supplier. Verify that no quantity is duplicated, unresolved return
quantity reaches zero and the financial credit remains an independent, traceable action.

**Acceptance Scenarios**:

1. **Given** an open return announcement against a delivered customer commitment, **When** goods
   arrive, **Then** the return movement names both the announcement and original delivery context and
   the arrived quantity is visible.
2. **Given** arrived return quantity, **When** the operator records one or more dispositions, **Then**
   each quantity is retained with its stated decision and destination and the sum cannot exceed the
   undisposed arrived quantity.
3. **Given** only part of a return has a disposition, **When** the return is viewed, **Then** the
   unresolved quantity remains visible and can continue to raise the existing operational exception.
4. **Given** a customer credit is recorded before or after physical return, **When** either side is
   inspected, **Then** the UI explains goods and money separately and preserves the appropriate
   returned-not-credited or credited-not-returned exception until both stated processes are complete.
5. **Given** a return-to-supplier disposition, **When** the goods leave, **Then** the outbound movement
   is traceable to the customer return and supplier context without inventing a supplier credit.

---

### User Story 4 - Explain Every Covered Movement (Priority: P3)

An operations reviewer can open every movement produced by the B2B story and understand why it
exists. Receipts and shipments point to commitments, returns point to their announcement and
delivery, corrections point to the record they replace, and exceptional adjustments retain a human
reason. Nothing in the shipped story appears as unexplained activity.

**Why this priority**: Autonomous decisions require trustworthy movement provenance, but this slice
can follow the commercial and returns paths once their relationships exist.

**Independent Test**: Run the multi-day B2B story and inspect every movement. Each movement has at
least one allowed explanation path and the unexplained-movement exception is empty for the story.

**Acceptance Scenarios**:

1. **Given** a movement created by a covered workflow, **When** its explanation is opened, **Then** it
   reaches its commitment, return announcement, correction, source record or explicit adjustment
   reason through the shortest available relationship.
2. **Given** a movement with none of those explanations, **When** it is recorded, **Then** the product
   warns before confirmation and the canonical exception remains visible afterward if confirmed.
3. **Given** the shipped B2B story, **When** all operational exceptions are evaluated, **Then** no
   unexplained movement originates from the story itself.

### Edge Cases

- A source invoice contains duplicate, missing or reordered line references.
- One delivery is billed by several partial invoices, or one invoice bills several deliveries.
- A price-only invoice line has no quantity and therefore cannot consume inventory cost.
- Invoice currency differs from retained acquisition-cost currency and no reviewed conversion basis
  exists.
- A supplier commitment is assigned to demand and later reduced below the assigned quantity.
- A customer commitment or supplier commitment is cancelled after a supply assignment exists.
- Returned quantity arrives in several parcels or exceeds the still-announceable delivered quantity.
- A return disposition is corrected after stock has already moved.
- Credit is issued without goods being required back, or goods return without a credit being due.
- The same confirmation or source event is retried after an unknown response.
- Projection refresh is delayed; the last completed result remains visible and states its freshness.
- A referenced record is archived, corrected or belongs to another company.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST retain every stated sales and supplier invoice line created or received
  through the covered B2B workflows, including quantity, unit, stated monetary values, item when
  stated, document relationship and source-line evidence when available.
- **FR-002**: The system MUST link an invoice line to the shortest existing operational scope it
  bills; it MUST NOT duplicate document, source or line relationships on downstream Reality records.
- **FR-003**: The system MUST support partial and multiple invoicing without treating unbilled or
  undelivered quantities as revenue or consumed cost.
- **FR-004**: For a supported invoiced sale, the system MUST expose received net revenue, exact
  retained acquisition cost consumed, DB1, reviewed selling costs and DB2 at invoice-line and invoice
  scopes.
- **FR-005**: A missing, stale, ambiguous, unreviewed or unsupported contribution basis MUST produce
  an unavailable result with machine-readable reasons and user-facing next steps; it MUST never be
  presented as zero.
- **FR-006**: Initial contribution projections for a newly completed business workflow MUST be
  prepared without requiring the user to press a first-refresh button.
- **FR-007**: A purchaser MUST be able to state quantity-based supply assignments from an open
  supplier commitment to compatible customer delivery commitments and to state the remainder as
  stock replenishment or unassigned.
- **FR-008**: Supply assignment MUST remain distinct from physical receipt, inventory reservation and
  fulfilment; no one of these records may imply another.
- **FR-009**: Supply assignment totals MUST not exceed the supplier commitment's remaining quantity
  or a customer commitment's remaining demand and MUST enforce company, item and relevant location
  compatibility.
- **FR-010**: Purchasing, sales and inventory reads MUST show assigned customer supply, stock
  replenishment, unassigned supply, received quantity and open quantity without double counting.
- **FR-011**: An operator MUST be able to record quantity-based dispositions for arrived customer
  returns using restock, quarantine/repair, scrap/loss or return-to-supplier decisions.
- **FR-012**: Return dispositions MUST not exceed undisposed arrived quantity, MUST support partial
  resolution and MUST remain correctable through explicit reversal or replacement rather than
  rewriting retained history.
- **FR-013**: Physical return disposition and customer/supplier financial credits MUST remain
  independent and the existing mismatch exceptions MUST remain visible until their own evidence is
  complete.
- **FR-014**: Every movement created by the covered workflows MUST expose an explanation through a
  commitment, return announcement, correction relationship, source record or explicit reason.
- **FR-015**: Recording an otherwise unexplained movement MUST present a clear warning before
  confirmation and MUST not suppress the canonical unexplained-movement exception.
- **FR-016**: The product MUST provide an executable, deterministic business story beginning with an
  empty company and covering immediate fulfilment, shortage, customer-specific procurement, stock
  replenishment, partial receipt, partial and final shipment, cancellation before shipment, sales
  invoice, supplier invoice, partial payment, announced return, arrived return, disposition, credit
  and contribution.
- **FR-017**: The story MUST use one consistent family per human-facing business number type, unique
  numbers within the company, non-zero commercially plausible prices and costs, and business dates
  on every document.
- **FR-018**: The story MUST identify intentional open exceptions separately from missing or broken
  setup and MUST provide exact references and UI paths for inspecting every expected outcome.
- **FR-019**: All mutating operations MUST preserve existing preview, confirmation, idempotency,
  authorization and retry semantics across Web, CLI, tools and agents.
- **FR-020**: Reads MUST keep the last completed answer visible with calculation freshness while an
  update is running and MUST not present stale data as current after a failed calculation.

### Domain and Traceability Requirements

- **DR-001**: Received document values remain Source → Evidence and are never recomputed. Contribution,
  open quantity, supply coverage and unresolved return quantity are derived observations from the
  retained records available at read time.
- **DR-002**: Invoice lines remain DocumentLine evidence. Revenue/cost matching and review records
  refer to the narrowest line or movement basis; no derived amount becomes new source authority.
- **DR-003**: A supply assignment relates a supplier Commitment directly to a customer Commitment or
  an explicit stock purpose. It MUST NOT use human numbers as identity or duplicate their Document,
  DocumentLine or SourceRecord links.
- **DR-004**: A return disposition relates directly to the arrived return movement or return
  announcement scope it resolves. The resulting physical movement remains authoritative for stock;
  the disposition is not a stored stock balance.
- **DR-005**: Every business record and relationship introduced by this feature is company-scoped;
  every read, write and constraint enforces that scope without foreign-company disclosure.
- **DR-006**: Web, CLI, agent and executable story paths call the same application services and
  business rules. Browser code and scenario fixtures MUST NOT implement alternative calculations.
- **DR-007**: Existing immutable source, document, movement, journal and reviewed-cost history remains
  immutable; corrections create explicit new evidence or revisions.
- **DR-008**: Any proposed new stored field or entity requires the plan to prove repeated calculation,
  filtering, joining, constraint or action use and to reject a shorter existing relationship first.

### Key Entities *(when data is involved)*

- **Invoice and Invoice Line**: Received commercial evidence, including the source-stated values and
  the operational scope billed by each line.
- **Customer Delivery Commitment**: The company's promise to deliver an item quantity to a customer;
  the demand side of an explicit supply assignment.
- **Supplier Delivery Commitment**: A supplier's promise to deliver an item quantity; the supply side
  that may be assigned to customer demand or stock.
- **Supply Assignment**: A stated quantity relationship between supplier supply and customer demand,
  or an explicit stock-replenishment purpose. It is neither receipt nor reservation.
- **Return Announcement**: The customer's stated intent to return quantity against a delivery.
- **Return Disposition**: A retained decision for arrived return quantity, connected to the physical
  movement that implements it.
- **Movement**: Immutable physical quantity evidence whose explanation is derived from its shortest
  retained relationships.
- **Contribution Observation**: A current read-time explanation of revenue, consumed acquisition
  cost, DB1, reviewed selling costs and DB2; it is not source authority.

## Success Criteria *(mandatory)*

- **SC-001**: A user can start with an empty company and complete the reference B2B story with all
  expected order, purchasing, warehouse, finance and return results visible in under 15 minutes of
  guided interaction.
- **SC-002**: Every supported delivered and invoiced story line shows a non-zero, arithmetically
  reconciling DB1; every line with reviewed selling costs also shows DB2, and no missing basis is
  displayed as EUR 0.00.
- **SC-003**: Across the reference story, invoice quantities, delivered quantities, consumed-cost
  quantities and credited quantities reconcile exactly, including partial invoices and returns.
- **SC-004**: For every supplier commitment in the story, customer-assigned, stock-replenishment,
  unassigned and already received quantities reconcile without overlap to the stated supply.
- **SC-005**: A five-unit mixed-disposition return can be completed with all five units accounted for,
  zero quantity duplicated and any intermediate unresolved quantity visible.
- **SC-006**: Every movement in the reference story reaches an allowed explanation in at most two
  user navigation steps; the story produces zero unexplained-movement exceptions.
- **SC-007**: A first-time user can identify the customer order, protecting supply, current stock,
  open receivable/payable, return state and DB explanation using documented references without
  database access or developer assistance.
- **SC-008**: Replaying any confirmed story action with the same request identity produces no
  duplicate business record, quantity, posting, invoice line or human-facing number.
- **SC-009**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The primary user is the existing Head of Operations persona with financial literacy and access to
  the current Sales, Purchasing, Warehouse, Finance and Inspector surfaces.
- Existing order, commitment, reservation, movement, document, settlement, costing, contribution,
  return-announcement, exception and projection services remain the authoritative foundation.
- One supplier commitment may serve several customer commitments and stock, but assignments are
  explicit quantities rather than an automatic allocation algorithm.
- Stock replenishment is an explicit purpose for the unassigned supply quantity; it does not require
  a forecast, reorder rule or warehouse bin model.
- Quarantine/repair may use an existing non-sellable location where that is sufficient. The plan must
  justify any new persisted state instead of assuming one.
- Return-to-supplier records physical outbound goods; a supplier credit remains separate evidence.
- The first implementation targets one company and one base unit per assignment relationship.
  Currency conversion continues to require the existing reviewed conversion basis.
- Existing historical records are not backfilled by inference. They remain unavailable or
  unexplained until explicit evidence or correction is recorded.
- The ordinary company-creation contract, shared job registry and materialized projection lifecycle
  remain unchanged except where initial contribution readiness requires an existing projection to be
  included in normal preparation.

## Open Questions

None. The defaults above intentionally keep procurement assignment manual, financial credits
separate from goods and all derived values non-authoritative.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-006, DR-001–DR-002 | US1 scenarios 1–5 | Service and business-story proofs for full/partial invoice lines, retained cost, DB1/DB2, missing basis and initial readiness |
| FR-007–FR-010, DR-003, DR-005 | US2 scenarios 1–5 | `packages/reality-core/tests/test_supply_assignments.py` tenant-isolated assignment tests plus customer-specific, stock and split-supply business story |
| FR-011–FR-013, DR-004, DR-007 | US3 scenarios 1–5 | Mixed return-disposition, over-disposition, correction and independent-credit tests |
| FR-014–FR-015 | US4 scenarios 1–3 | Movement explanation and unexplained-movement warning/exception tests |
| FR-016–FR-018 | US1–US4 independent tests | Deterministic empty-company B2B scenario and bilingual catalog/UI navigation evidence |
| FR-019–FR-020, DR-006 | All stories | Cross-adapter parity, confirmation/idempotency and projection freshness tests |
| DR-008 | Architecture review | Plan data-model proof and shortest-relationship review |
| SC-001–SC-009 | Full acceptance run | Timed browser journey, reconciliation assertions and complete requirement-to-test matrix |
