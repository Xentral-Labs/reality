# Feature Specification: Invoices state net and tax

**Feature Branch**: `284-invoice-net-tax`
**Created**: 2026-09-26
**Status**: Draft
**Language**: English
**Input**: "Create the spec for the invoice form." It comes from the spec 282 live
walk-through: a sales invoice recorded through the web form cannot produce DB1.

## Context and Intent

### Problem

DB1 is received net revenue less the confirmed goods cost. Reality takes the net amount of an
invoice line as the invoice states it (`DocumentLine.payload.reality_finance_v1.net`) and
never computes it from gross (Constitution VIII).

The web invoice form (`InvoiceCard`, used for customer and supplier invoices) asks only for
a gross amount per position. The 282 walk-through (`specs/282-cost-review-draft/quickstart.md`)
recorded order SO-282, a goods issue and invoice INV-282 through the product. The
contribution preview then reports `received_net_missing`: DB1 can never be proven for any
invoice recorded in the web. Only imported or seeded invoices carry a stated net.

The core already accepts the stated amounts for multi-position invoices (`lines[*].reality_finance_v1`
with `net`, `tax`, `base`, `gross`). The gap is elsewhere:
- the single-position path of `record_sales_invoice` does not take `reality_finance_v1`;
- the delivery review may drop the stated amounts on the way to the stored invoice;
- the web form never asks for net or tax.

The same form records supplier invoices, whose receipt cost evidence also reads the stated
basis. Knowing the net amount lets a receipt be costed without guessing whether tax is
included.

### Scope

- **Invoice form:** optional net and tax amounts per position, as the invoice states them,
  for customer and supplier invoices.
- **Invoice path:** these amounts flow unchanged into the reviewed intent, the confirmed
  invoice's stored source and each invoice line's `reality_finance_v1`. This covers the
  single-position and the multi-position path through the web, MCP and chat.
- **Consistency:** when net, tax and gross are all given, the service compares these
  received values and refuses a contradiction instead of storing it. A comparison is not a
  recomputation, and no amount is derived from another.
- **Result:** an invoice recorded with a stated net makes DB1 provable through the spec 282
  contribution draft.

### Non-Goals

- Computing net or tax from gross, a tax rate or a tax code. Reality records what the
  invoice states.
- Tax codes, rates, tax reporting or posting net and tax to separate ledger accounts. The
  existing posting stays on gross.
- Correcting invoices recorded earlier. They keep their gross-only evidence, and a new
  invoice or a credit plus new invoice follows the existing correction path.
- Free supplier invoices without an order (`supplier_invoice_free_record`). They have their
  own form and contract.
- Making net or tax mandatory. Businesses that invoice without tax detail keep recording
  gross only.
- An invoice-level net or tax total. Amounts are stated per position only (owner decision).

### Existing Contracts

- `docs/features/order_to_cash.md` and `docs/features/procure_to_pay.md`: invoice entry.
- `docs/features/receipt-costing.md`: the received finance detail contract and DB1.
- Spec 120 (unified invoice entry), 122 (multi-position invoices) and 124 (partial
  invoicing).
- Spec 282: the contribution draft that needs a stated net.
- Constitution VIII (received values are recorded, never recomputed; comparing received
  values is encouraged).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A customer invoice states its net amount (Priority: P1)

A clerk records invoice INV-282 for 2 lamps: gross 59.50 EUR, of which net 50.00 and tax
9.50, as printed on the invoice. The review shows the three stated amounts, and the clerk
confirms. The invoice line's cost explanation then offers "Prepare the contribution review",
and DB1 can be proven.

**Why this priority**: Without it DB1 is impossible for every invoice recorded in the web.

**Independent Test**: Record a single-position sales invoice with net and tax through the
web path. The line's received detail carries the stated net and tax unchanged, and the
contribution preview is a candidate instead of `received_net_missing`.

**Acceptance Scenarios**:

1. **Given** a delivered order line, **When** an invoice is recorded with gross 59.50, net
   50.00 and tax 9.50, **Then** the invoice line's `reality_finance_v1` holds exactly these
   stated values and the contribution preview no longer reports `received_net_missing`.
2. **Given** the review of that invoice, **When** it is shown, **Then** it lists gross, net
   and tax, so the confirmation covers them.
3. **Given** net 50.00, tax 9.50 and gross 60.00, **When** the invoice is prepared, **Then**
   it is refused with a message naming the contradiction, and nothing is recorded.
4. **Given** an invoice with gross only, **When** it is recorded, **Then** it behaves exactly
   as today.

---

### User Story 2 - Multi-position invoices keep their stated amounts (Priority: P1)

An invoice with two positions states net and tax for each. Both lines carry their own
stated amounts after confirmation.

**Why this priority**: Real invoices have several positions. Losing detail on that path
would silently block DB1 again.

**Independent Test**: Record a two-position invoice with per-position net and tax through
the delivery review and confirmation. Each line's received detail equals its stated values.

**Acceptance Scenarios**:

1. **Given** two positions with their own net and tax, **When** the invoice is confirmed,
   **Then** each invoice line carries its position's stated amounts.
2. **Given** one position with net and tax and one without, **When** it is confirmed,
   **Then** only the first line carries stated amounts, and the second stays gross-only.

---

### User Story 3 - Supplier invoices state net and tax too (Priority: P2)

The same form records a supplier invoice for a purchase order line with stated net and tax.
Receipt cost evidence then reads the stated net, instead of a gross whose tax treatment is
unknown.

**Why this priority**: It is the same form and contract, and it removes a guess from receipt
costing.

**Independent Test**: Record a supplier invoice with net and tax. Its line carries the stated
amounts, and the cost evidence read offers the net basis.

**Acceptance Scenarios**:

1. **Given** a purchase order line, **When** a supplier invoice is recorded with net and tax,
   **Then** the invoice line's received detail holds them, and `cost_evidence` reports the net
   basis as available.

### Edge Cases

- **Tax only, no net** (or the reverse): the stated value is recorded as it is, and nothing
  is derived.
- **Zero tax** (for example, a tax-exempt delivery): net equals gross, tax 0, both stated and
  consistent.
- **Precision**: amounts follow the existing four-decimal bound and are never rounded.
- **Currency**: stated amounts are in the invoice currency. A different currency in the
  detail is refused, as the received detail contract already does.
- **Replay and idempotency**: a retried request with the same stated amounts is the same
  proposal. Changed amounts need a new review.
- **Tenant boundary**: unchanged; the invoice path is already tenant-scoped.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The invoice form MUST offer optional net and tax amounts per position for
  customer and supplier invoices, labelled "as stated on the invoice".
- **FR-002**: The single-position invoice path (`record_sales_invoice`,
  `record_supplier_invoice`, their tools, MCP schemas and the delivery review) MUST accept the
  stated amounts as `reality_finance_v1` and pass them on unchanged.
- **FR-003**: The multi-position path MUST keep each position's stated amounts through
  preview, review, confirmation and the stored invoice lines.
- **FR-004**: When a position states net, tax and gross, the service MUST refuse the invoice
  if net plus tax differs from gross. It MUST NOT adjust any value.
- **FR-005**: The review MUST show the stated net and tax next to gross, so the person
  confirms them.
- **FR-006**: An invoice without net or tax MUST behave exactly as today.
- **FR-007**: A sales invoice line with a stated net MUST let the contribution preview
  proceed past `received_net_missing`.

### Domain and Traceability Requirements

- **DR-001**: The stated amounts are received evidence. They MUST be stored as received in
  the invoice's SourceRecord and the invoice line's `reality_finance_v1`, and MUST never be
  derived from each other or from a rate (Constitution VIII).
- **DR-002**: No new table or typed column. The existing `DocumentLine.payload.reality_finance_v1`
  contract (version 1) carries the values.
- **DR-003**: Web, MCP and chat MUST use the same invoice services. No adapter may compute
  or fill a missing amount.
- **DR-004**: Posting stays on the stated gross. The stated net and tax change no ledger
  entry in this feature.

### Key Entities

- **Stated invoice amounts**: the net, tax and gross an invoice position states, recorded as
  received evidence.

## Success Criteria *(mandatory)*

- **SC-001**: Re-running the spec 282 live walk-through with an invoice recorded through the
  web form with stated net and tax reaches a proven DB1. Nobody types an identifier.
- **SC-002**: No existing gross-only invoice flow changes behavior (existing invoice suites
  stay green).
- **SC-003**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- `reality_finance_v1` (version 1) with `net`, `tax`, `base`, `gross` and `currency` is the
  received detail contract (`services/finance/components.py`); this feature adds no field.
- The multi-position path already validates `reality_finance_v1` per position
  (`services/core.py`). Whether the delivery review and preview keep it end to end is to be
  verified in the plan; FR-003 holds either way.
- Spec 282 is merged or merges first; SC-001 relies on its contribution draft.

## Open Questions

None. Decided by the owner on 2026-09-26: net and tax are asked per position only; there is
no invoice-level net or tax total.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1, US3 | web contract and browser test of the form |
| FR-002 | US1 1 | single-position service and review test |
| FR-003 | US2 1–2 | multi-position review and confirmation test |
| FR-004 | US1 3 | contradiction refused, nothing recorded |
| FR-005 | US1 2 | review shows stated amounts |
| FR-006 | US1 4 | existing invoice suites; gross-only test |
| FR-007 | US1 1 | contribution preview is a candidate |
| DR-001 | US1 1 | stored source and line detail equal the stated values |
| DR-002 | — | plan schema review: no migration |
| DR-003 | US1–US3 | MCP and web parity test |
| DR-004 | US1 | ledger entries unchanged versus a gross-only invoice |
