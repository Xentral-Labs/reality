# Feature Specification: Open items default order

**Language**: English

## Context and Intent

### Problem

Every workspace register that lists documents or movements shows the newest record first
by default: customer and supplier orders by document date, warehouse movements and
reservations by posting time, and the Finance payments and journal registers by effective
time. The Finance open items register is the one exception. It reads the materialized
`open_financial_items` projection, and the projection page falls back to the projection
record key, which is the opaque document identifier. Document identifiers are random, so the
open items a user sees first have no relation to when they were recorded. The register also
shows no date column, so the user cannot tell why rows appear in that order or recover the
chronology by sorting.

### Scope

One default order for the Finance open items register and one Date column that makes the
order visible and sortable. Receivables and payables share the default. The credit flows on
the same page (customer credit, customer and supplier balance) keep their own default and
gain the same Date column because they render the same table.

### Non-Goals

No change to the default order of any other register. Deliveries and commitments are work
queues and stay ordered by due date, oldest first. Payments, journal, movements,
reservations, orders, inventory and master data keep their current defaults. No new sort
keys, no aging or dunning view, no change to totals, filters, paging or the projection
schema.

## User Scenarios & Testing

### US1 — See the latest invoice after posting it

A finance user posts a customer invoice and opens Finance › Open items.
Acceptance: the new invoice is the first row of the receivables register without paging
or sorting.

### US2 — Understand the order

A finance user scans the open items register.
Acceptance: a Date column shows each item's document date, and the rows are in descending
document date order; clicking the Date header switches to ascending order and back.

### US3 — Deliveries stay a work queue

A user opens Sales › Deliveries after this change.
Acceptance: deliveries are still ordered by due date with the oldest first.

### Edge Cases

- Two items with the same document date keep a stable order across pages (record key breaks
  the tie).
- An item without a document date shows an em dash in the Date column and sorts last when
  sorting by date explicitly.

## Requirements

- **FR-001**: When the open items register is requested without an explicit sort, the
  `open_financial_items` projection page orders rows by document date descending, then by
  record key, before paging. Totals are unaffected.
- **FR-002**: The default is declared per projection. Other projections keep the record key
  default unless they declare their own.
- **FR-003**: The Finance open items table shows a Date column between the invoice column and
  the amount columns. The column is sortable by the existing `date` sort key.
- **FR-004**: The numeric columns of the open items table remain right-aligned after the
  column is inserted.

## Success Criteria

- A register test posts three invoices with different document dates and receives them
  newest first without a sort parameter, and oldest first with `sort=date&sort_direction=asc`.
- The Finance browser suite passes with the shifted numeric column indices.

## Assumptions and Dependencies

- The projection payload stores `document_date` as an ISO date string, so text order equals
  chronological order.
- The register uses the shared `RegisterTable` profile, so the Date column is added there and
  in the Finance page header and row in step.
- The `Date` label already exists in every supported language.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-002 | US1, US3, edge cases | `packages/reality-core/tests/test_unified_table_queries.py::test_open_items_default_to_newest_document_first` |
| FR-003, FR-004 | US2 | `apps/web/scripts/unified-finance-browser.mjs` numeric alignment matrix |
