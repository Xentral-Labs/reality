# Feature Specification: Invoice Settlement Dates in One Read

**Feature Branch**: `384-invoice-settlement-dates`
**Language**: English
**Created**: 2026-10-11
**Status**: Approved
**Input**: An order-to-cash agent connected over MCP needs, for one invoice that has been paid, its
due date, its open amount and the allocations that settled it with their dates. No bounded read
returns all three.

## Context and Intent

### Problem

An external agent checking whether a customer paid an invoice on time asks three things about one
invoice: when it was due, what is still open, and which payments or credits settled it and when.

`finance_settlement_context` already selects one invoice by its opaque ID and returns its open
amount, but neither its due date nor the allocations behind that open amount. The aging register
holds the due date, but no MCP read exposes it for one invoice, and the aging views a client can
reach list open items, so a fully paid invoice drops out of them. The settlement register holds
dated allocation links company-wide, but it is not exposed for one invoice and it does not exclude
allocations whose payment was later reversed.

The Business Recorder (`graph_ask`) was tried first against a paid invoice. It returns the due date
and open amount from the customer position node, and allocation sums by `allocated_at` along the
`settles` edge, but only as two separate client-composed questions, grouped rather than one row
per allocation, without the paying document's identity, and it still reports an allocation after
its payment was reversed while the open amount is back at the full invoice amount (research in
`plan.md`). It is an analytics surface, not an operational read a client can rely on.

### Scope

Extend the invoice answer of `finance_settlement_context` with the invoice's due date and the
active allocations that settle it, each with the crediting document's opaque ID, its number as a
label, its type, the allocated amount, when the allocation was recorded and when the crediting
entry took effect.

### Non-Goals

- No new tool, no new table, column or migration.
- No change to the credit branch of the same read, to how open amounts are derived, or to any
  mutation.
- No on-time verdict, days-late figure or payment-behavior score; the client compares the dates.
- No change to `graph_ask`, the reporting graph or the settlement register.

## User Scenarios & Testing

### User Story 1 - A paid invoice explains its own settlement (Priority: P1)

As an order-to-cash agent, I read one invoice and receive its due date, its open amount and every
active allocation that settled it with its dates, so I can tell whether it was paid on time
without composing a query.

**Why this priority**: It is the whole feature; without it the client needs two analytics queries
whose answers disagree after a reversal.

**Independent Test**: Record a dated invoice with a payment term, settle it with two dated
payments, and read `finance_settlement_context` at the service and through the MCP tool.

**Acceptance Scenarios**:

1. **Given** an invoice dated 2026-09-01 with a 14-day term, settled by payments effective
   2026-09-10 (60) and 2026-09-20 (40), **When** it is read, **Then** the answer states due date
   2026-09-15, open 0 and two allocations with each payment's document ID, number, amount,
   recording time and effective time, ordered by effective time.
2. **Given** one of those payments is reversed, **When** the invoice is read again, **Then** that
   allocation is absent, the other remains and the open amount equals the reversed amount.
3. **Given** the same invoice read through the MCP tool, **Then** the answer is identical to the
   service answer.

### Edge Cases

- An invoice without any payment term is due on its own document date; one without a document date
  states no due date.
- A customer fee claim states no due date, because no fee source states one (spec 318).
- An opening debt states its recorded original due date.
- An unsettled invoice returns an empty allocation list.
- A settlement reduction or credit note allocated to the invoice appears as an allocation with its
  own document type, so a client can tell cash from noncash settlement.

## Requirements

### Functional Requirements

- **FR-001**: The invoice answer of `finance_settlement_context` MUST include `due_date`, taken
  from the same shared due-date rule the aging register uses, or null where that rule states none.
- **FR-002**: The invoice answer MUST include `allocations`: every active allocation against the
  invoice's settlement control entry, as returned by the same shared reader that derives the open
  amount, each with `allocation_id`, `document_id`, `document_number`, `document_type`, `amount`,
  `allocated_at` and `effective_at`.
- **FR-003**: Allocations whose payment or credit posting was reversed MUST NOT appear, so the
  allocations and the open amount never contradict each other.
- **FR-004**: Every value MUST be read from recorded allocations, ledger entries and documents of
  the caller's company; nothing is stored and no amount is recomputed.
- **FR-005**: The MCP tool MUST return the same answer as the service.

### Key Entities

- **Allocation**: an existing settlement allocation linking a crediting ledger entry to the
  invoice's control entry with a stated amount and a recording time.

## Success Criteria

### Measurable Outcomes

- **SC-001**: One `finance_settlement_context` call answers due date, open amount and dated
  allocations for a paid invoice.
- **SC-002**: After a payment reversal, the sum of returned allocations plus the open amount equals
  the invoice's gross amount in an executed test.

## Assumptions and Dependencies

- `allocated_at` is knowledge time (spec 232 FR-003); `effective_at` of the crediting entry is the
  stated payment time a client compares with the due date. Both are returned and named as such.
- The due date is a read-time observation from the stated document date and stated payment term,
  or the stated original due date for opening debts; it is not stored (constitution principle VIII).
- Allocations per invoice are few; the list is not paginated.

## Requirement Traceability

FR-001, FR-002, FR-004 → US1 scenario 1. FR-003 → US1 scenario 2 and SC-002. FR-005 → US1
scenario 3.
