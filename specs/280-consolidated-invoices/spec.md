# Feature Specification: Consolidated invoices across orders

**Language**: English
**Created**: 2026-09-26
**Status**: Accepted by the owner on 2026-09-26 (see Clarifications).

## Context and Intent

### Problem

A supplier sends one invoice for goods ordered on two purchase orders, and a wholesale
customer expects one monthly invoice for all deliveries. The guided invoice entry refuses
both: every selected position must belong to the same order ("Invoice positions must belong
to the same order."). Specs 120, 122 and 124 kept multi-order consolidation out of scope on
purpose.

The model already supports it. Spec 076 put the invoice-to-order link on the line
(`DocumentLine.billed_document_line_id`) so that "a consolidated invoice covering several
orders, which is ordinary B2B billing" is expressible, and billing arithmetic sums every
referencing line. The free supplier invoice path already records such an invoice (scenario
catalog I05, `tests/scenarios/test_catalog_purchasing.py`). Only the guided entry and the
reads built on the one-order assumption are missing.

Scenario catalog rows: I05 (supplier invoice over two purchase orders) and E02 (monthly
collective sales invoice), `docs/scenarios/catalog.md`.

### Scope

Record one customer or supplier invoice whose positions come from several orders of the
same party, through the existing guided entry, review and confirmation flow, and keep every
read that follows an invoice to its order truthful when there is more than one.

### Non-Goals

- No tax, price, discount or total calculation; line amounts and the header total stay
  stated (Constitution VIII).
- No invoice editing after confirmation; corrections stay reversal plus rebilling (spec 124).
- No invoice across parties or across currencies.
- No automatic proposal of what to invoice (no billing run, no "invoice all open
  deliveries" job).
- No new document type, status field or schema; the existing line link carries the relation.
- No change to credit notes; crediting across orders is already line-based (spec 079).
- No XRechnung/ZUGFeRD interpreter; received e-invoices stay lossless source artifacts
  (catalog E10).

## User Scenarios & Testing

### US1 — Record one supplier invoice over several purchase orders (P1)

A clerk receives one supplier invoice that bills goods from two purchase orders. They pick
positions from both orders of that supplier, enter each stated quantity and line amount and
the stated invoice total, review once and confirm once.

**Independent Test**: two purchase orders of one supplier, received in part; one invoice
with one position from each order is recorded through the guided tool.

**Acceptance Scenarios**:

1. **Given** received positions on PO-A and PO-B of one supplier, **When** one invoice with a
   position from each is confirmed, **Then** one invoice, one line per position linked to its
   order line, and one balanced posting group at the stated total are recorded.
2. **Given** that invoice, **When** each purchase order is inspected, **Then** each shows
   exactly its own billed and remaining quantity, and both name the same invoice.
3. **Given** a position of another supplier or another currency, **When** it is added,
   **Then** the review refuses it before any write and names the reason.

### US2 — Record one monthly customer invoice over several orders (P1)

A clerk bills all of a customer's delivered positions of the month on one invoice. They pick
positions from several sales orders of that customer and confirm once.

**Acceptance Scenarios**:

1. **Given** shipped positions on three orders of one customer, **When** one invoice over all
   three is confirmed, **Then** `shipped_not_billed` clears for each order line by its own
   quantity.
2. **Given** a prepayment order whose positions are billed on a consolidated invoice, **When**
   fulfilment readiness is read, **Then** the order is released only once the consolidated
   invoice is settled in full, and the invoice is not treated as ambiguous merely because it
   bills another order too.
3. **Given** a payment naming one of the orders, **When** it is interpreted, **Then** it is
   not silently allocated to the whole consolidated invoice; it becomes a candidate with a
   reason, or allocates by the invoice reference.
4. **Given** that consolidated invoice paid in part, **When** readiness is read, **Then** every
   prepayment order it bills stays blocked with a reason naming the invoice and its open
   amount.

### US3 — Review, recover and explain consistently (P1)

The consolidated invoice is reviewable and recoverable from Finance, Actions, Chat and
Decisions exactly like a one-order invoice, and the Inspector leads from the invoice to each
order and from each order back to the invoice.

**Acceptance Scenarios**:

1. **Given** a reviewed consolidated invoice, **When** any selected position changes or is
   billed elsewhere before confirmation, **Then** the review is stale and nothing is written.
2. **Given** a failed later position, **When** confirmation runs, **Then** no invoice, line or
   posting exists (atomic).
3. **Given** a one-order invoice proposal or receipt from before this feature, **When** it is
   reviewed or replayed, **Then** it behaves exactly as today.

### Edge Cases

- Positions from two orders of the same party in different currencies.
- The same order line selected twice, or across two concurrent reviews.
- An order line already fully billed by another invoice (spec 124 boundary unchanged).
- An order whose ship-to party differs from the orderer (bill-to stays the order party).
- A consolidated invoice reversed later: every order line becomes billable again by its own
  quantity.
- A cancelled commitment on one of the orders between review and confirmation.
- 50 or more positions from 12 or more orders (spec 076 SC-002 example); more than 200
  positions are refused (FR-010).

## Requirements

- **FR-001**: The shared invoice preview MUST accept positions from several orders when they
  share direction, party and currency, and MUST refuse mixed parties, currencies, directions
  or tenants before any write.
- **FR-002**: Confirmation MUST record one lossless manual source, one invoice, one line per
  position linked by `billed_document_line_id`, and one balanced posting group at the stated
  total, atomically, without recomputing any received value.
- **FR-003**: Billing reads (billed and remaining per order line, `shipped_not_billed`,
  `billed_not_received`, `invoice_price_differs`) MUST attribute each invoice line to its own
  order line only.
- **FR-004**: Fulfilment readiness for prepayment MUST NOT treat an invoice as ambiguous only
  because it also bills another order of the same party. A prepayment order billed on a
  consolidated invoice is released only when that invoice is settled in full; while it is
  open, the blocker names the invoice and its open amount. No payment is split across orders.
- **FR-005**: Payment interpretation by order reference MUST NOT allocate to a consolidated
  invoice on the order reference alone; it MUST produce a candidate with a stated reason.
  Allocation by the invoice reference is unchanged.
- **FR-006**: The guided entry MUST let the clerk choose a party and currency and pick
  positions from a party-wide list of billable order positions (delivered or received and not
  yet fully billed), grouped by order. The existing one-order entry remains available.
- **FR-007**: Review, stale-review detection, recovery, Chat, MCP input schema, the Decision
  trail and the CLI where an invoice command exists (none today) MUST use the same shared
  services; the MCP schema declares the nested
  positions; `make docs-generate` output is updated.
- **FR-008**: The Inspector MUST lead from a consolidated invoice to every order it bills and
  from each order to the invoice, through the line links only.
- **FR-009**: Existing one-order proposals, receipts and tools MUST keep their contracts.
- **FR-010**: One invoice MUST carry at most 200 positions, the same bound as the
  billable-positions read; core refuses more before any write and the MCP schema declares it.

## Key Entities

Existing SourceRecord, Document (`sales_invoice`, `supplier_invoice`), DocumentLine with
`billed_document_line_id`, LedgerEntry, SettlementAllocation, ChangeProposal and
BusinessEvent. No new entity, field or status.

## Success Criteria

- **SC-001**: One supplier invoice over two purchase orders and one customer invoice over
  three sales orders are entered, reviewed, confirmed and inspected through the guided flow.
- **SC-002**: Per order line, billed plus remaining equals the order quantity before and after
  a consolidated invoice and after its reversal.
- **SC-003**: No read derives a single order for a consolidated invoice; readiness and payment
  matching give a stated reason instead of a silent choice.
- **SC-004**: Catalog rows I05 and E02 move to covered; existing single-order journeys and all
  required gates pass.

## Assumptions and Dependencies

- Spec 076 line-level linking is the authority for the invoice-to-order relation; spec 122
  and 124 validation of each position stays in force per position.
- The free supplier invoice path already proves that consolidated supplier invoices post and
  bill correctly; this feature brings the guided entry and the dependent reads to the same
  level.
- Web changes follow `docs/WEB_SPEC.md`, four languages and the shared review card.

## Clarifications

### Session 2026-09-26 (owner)

- Q1 Scope: both directions in one feature → **Both**; the service change is shared.
- Q2 Grouping: → **One party and one currency per invoice.** Prepayment release: →
  **Released only when the consolidated invoice is settled in full**; no proportional split.
- Q3 Entry: → **Party-wide list of billable positions**, grouped by order.
- Q4 Non-goals: → **List confirmed**; an XRechnung/ZUGFeRD interpreter stays out of scope.

## Requirement Traceability

| Requirement | Story | Tests |
|---|---|---|
| FR-001, FR-002 | US1, US2 | shared invoice preview/confirmation service tests, both directions |
| FR-003 | US1 scenario 2, US2 scenario 1 | billing and exception derivation tests per order line |
| FR-004 | US2 scenarios 2, 4 | fulfilment readiness prepayment tests with a consolidated invoice, full and partial payment |
| FR-005 | US2 scenario 3 | payment intake order-reference test |
| FR-006 | US1, US2 | web invoice entry tests |
| FR-007, FR-009 | US3 | review/stale/recovery, MCP, CLI and legacy-proposal tests |
| FR-008 | US3 | Inspector link tests |
| FR-010 | US1, US2 | position bound test in core and MCP schema |
