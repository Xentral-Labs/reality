# Feature Specification: Party balances

**Feature Branch**: `170-party-balances`
**Created**: 2026-09-11
**Status**: Draft
**Language**: English
**Input**: "Wo genau sehe ich, wenn jemand zu viel bezahlt hat? So eine richtige Liste gibt es nicht: pro Kunde und Lieferant, was gesamt offen oder als Guthaben da ist."

## Context and Intent

### Problem

Reality answers "what is open" per document and "what credit is available" per document. It does
not answer the question every accounts clerk asks first: **per customer, per supplier, where do we
stand?** Today that answer is assembled by hand from two registers: Open items lists each invoice
with its open amount, and the credit filter lists each overpayment and each credit note with its
available amount. A customer with three small overpayments appears three times; a customer who
owes 1,000 and holds 200 of credit appears in both lists and nowhere as 800. `finance_balances`
gives the company totals per currency, not the position of one party.

An ERP professional knows this list as the debtor and creditor balance list (Saldenliste,
Offene-Posten-Liste je Debitor). Its absence is the reason the receivables playbook's question
"who paid too much" is answered per receipt instead of per customer.

### Scope

- One derived, read-time view of balances per party and currency for the customer side and the
  supplier side: open amount, of which overdue, available credit, net balance, number of open
  documents, number of credit documents, oldest due date.
- Available in the App under Finance as its own view, with the same search, paging and sorting
  contract as the other finance registers, and with a drill-down into that party's open items and
  credits.
- Available to agents as a public read tool with the same numbers and the same guidance.
- Nothing is stored, computed forward or netted in the books: the view adds up what the open items
  register and the credit register already derive, per party.

### Non-Goals

- No netting posting, no automatic use of credit against open invoices; using credit stays the
  confirmed settlement of specs 148 and 168.
- No currency conversion: a party with open items in two currencies has two rows, as in
  `finance_balances`.
- No dunning levels, no aging buckets beyond "of which overdue"; an aging analysis is its own
  feature.
- No supplier statement reconciliation (comparing our balance with the supplier's statement).
- No change to the open items register, the credit filter or the payments register.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md), [workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md).
- Open items derivation (`financial_open_items`, projection `open_financial_items`), credit
  derivation (`available_credit_items`, spec 148 and 169), payment matching contract
  (`docs/features/payment_matching.md`, spec 168).
- `overdue_receivable` and `overdue_payable` judge overdue from the aging register
  (`aging_register`, one due-date rule for invoices and opening items); this view consumes the
  same register.
- Finance register contract of the unified App (spec 139 and 167): cursor pages, `q`, `sort`,
  `sort_direction`, totals unaffected by paging.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Where does this customer stand (Priority: P1)

A clerk opens Finance → Balances, side Customers, and sees one row per customer and currency:
Müller GmbH, EUR, open 1,000.00, of which overdue 240.00, credit 20.00, balance 980.00, 3 open
invoices, 1 credit, oldest due 3 September. Sorting by balance or overdue shows who matters today;
the search finds one customer by name.

**Why this priority**: It is the list the feature exists for and the one the clerk asks for first.

**Independent Test**: Post three invoices for one customer, pay one in full, one partially, and
overpay the third; assert one row with open, overdue (as of a date after one due date), credit,
balance and the two counts; assert another customer with nothing open produces no row.

**Acceptance Scenarios**:

1. **Given** a customer with open invoices and an overpayment, **When** the customer balances are
   read, **Then** one row shows open = sum of open amounts, credit = sum of available credit,
   balance = open − credit, counts and the oldest due date.
2. **Given** an invoice whose original due date is before the read's as-of instant, **When** the
   balances are read, **Then** its open amount is included in "of which overdue" and the row is
   sortable by that column.
3. **Given** a customer with items in EUR and USD, **When** the balances are read, **Then** two rows
   appear and nothing is converted.
4. **Given** a customer with nothing open and no credit, **When** the balances are read, **Then**
   the customer does not appear.

---

### User Story 2 - Who paid too much (Priority: P1)

The clerk sorts the customer balances by credit descending, or filters to "credit only", and sees
each customer once with their total available credit, not each receipt.

**Why this priority**: This is the owner's question; today it is answered per document.

**Independent Test**: Give one customer two overpayments and one credit note; assert one row whose
credit equals the sum of the three available amounts and whose credit count is three.

**Acceptance Scenarios**:

1. **Given** two overpayments and one booked credit note for one customer, **When** the balances
   are read with the credit filter, **Then** one row shows credit = the sum and credit count 3.
2. **Given** a credit that was used up by a later allocation, **When** the balances are read,
   **Then** it no longer counts.

---

### User Story 3 - From the balance to the documents (Priority: P2)

From a balance row the clerk opens that party's open items or credits and lands on the existing
registers filtered to the party.

**Why this priority**: The balance is a summary; the work happens on the documents.

**Independent Test**: The App's balance row links carry the party into the open items and credit
filters; the registers show only that party's rows.

**Acceptance Scenarios**:

1. **Given** a balance row, **When** the clerk opens its open items, **Then** the open items
   register shows that party's open documents only.
2. **Given** a balance row with credit, **When** the clerk opens its credits, **Then** the credit
   filter shows that party's credit documents only.

---

### User Story 4 - The same list for an agent (Priority: P2)

An agent asked "who owes us the most" or "which suppliers do we owe" reads the balances tool and
answers with parties and amounts, citing the read.

**Why this priority**: The receivables and purchasing playbooks need one read for "watch the money"
and "watch the supply side" instead of adding up documents.

**Independent Test**: The tool returns the same rows as the App view for the same tenant and side;
another tenant sees nothing; the tool is read-only and carries capability guidance.

**Acceptance Scenarios**:

1. **Given** the customer of US1, **When** `finance_party_balances` is read with side customer,
   **Then** the row matches the App view in every amount and count.
2. **Given** another tenant, **When** the tool is read there, **Then** it returns no rows.

### Edge Cases

- A party that is both customer and supplier appears on both sides with separate rows; nothing is
  netted across sides.
- A payment recorded without allocation and without an invoice (pure credit) counts as credit for
  its party; a party with credit and nothing open has open 0 and a negative balance.
- Reversed or voided documents are excluded exactly as the open items and credit registers
  exclude them; the view derives from those registers and adds no rule of its own.
- An invoice whose aging row has no due date (no term and no stated date) is never overdue and
  does not set the oldest due date.
- The as-of instant for "overdue" is the read's instant; the view is never stored.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Reality MUST derive, at read time, one row per party and currency for a given side
  (customer or supplier) with: open amount, overdue amount, available credit, balance
  (open − credit), open document count, credit document count and oldest due date.
- **FR-002**: Open and overdue MUST be taken from the same derivation as the open items register;
  credit MUST be taken from the same derivation as the credit filter; the view MUST NOT compute
  either independently.
- **FR-003**: Overdue MUST use the due date the aging register derives for the document (the
  payment-term rule for invoices, the stated original due date for opening items) against the
  read's as-of instant, the same rows and the same condition as `overdue_receivable` and
  `overdue_payable`.
- **FR-004**: Rows MUST be grouped by party and currency; no amount MUST be converted or added
  across currencies.
- **FR-005**: Parties with open 0 and credit 0 MUST NOT appear.
- **FR-006**: The App MUST show the view under Finance as a Balances view with a side selector,
  the register search, paging and sorting contract (sort keys: party, open, overdue, credit,
  balance, oldest due), and a "credit only" filter.
- **FR-007**: Each row MUST offer a drill-down into that party's open items and into that party's
  credits, reusing the existing registers with a party filter.
- **FR-008**: A public read tool `finance_party_balances(side, credit_only?, query?, limit?)` MUST
  return the same rows, tenant-scoped, without recording anything, with capability guidance that
  names when to use it and what it does not prove (it proves a position, not that a customer
  will pay or that a credit may be netted without confirmation).
- **FR-009**: The receivables and purchasing playbooks MUST name the view and the tool in their
  "watch" situations and in the overpayment situation.

### Domain and Traceability Requirements

- **DR-001**: No schema change; the view is a read-time derivation over existing ledger entries,
  allocations and documents.
- **DR-002**: Source → Evidence → Reality is unchanged; the view creates no record and no event.
- **DR-003**: Stated amounts are never recomputed; sums of stated amounts per party are
  aggregation, not derivation of new amounts (constitution rule on recomputation, spec 088
  DR-007).
- **DR-004**: Every row MUST be explainable: the drill-down shows exactly the documents whose
  amounts were added.

## Success Criteria *(mandatory)*

- **SC-001**: For the US1 fixture the row's amounts equal the sums a test computes from the open
  items and credit registers, and the counts match, in both the App view and the tool.
- **SC-002**: The Finance browser suite shows the Balances view, sorts by balance and overdue, and
  reaches the filtered open items from a row.
- **SC-003**: Tenant isolation test: the tool and the view return nothing for a foreign tenant.
- **SC-004**: The playbooks' "who paid too much" step reads one list per customer; the docs build
  passes.

## Assumptions and Dependencies

- The open items derivation carries `party_id`, `currency`, `open` and `original_due_date` per
  document, and the credit derivation carries party, currency and available amount per credit
  document; both exist today.
- The finance register contract (cursor pages, `q`, `sort`) is shared code and can host a new
  register without a new pattern.
- A party filter on the open items and credit registers exists or is a small addition to their
  query parameters.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-002, FR-004, FR-005 | US1 scenarios 1, 3, 4; US2 | `tests/finance/test_party_balances.py` |
| FR-003 | US1 scenario 2 | same file, overdue as-of test |
| FR-006, FR-007 | US1, US3 | `apps/web/scripts/unified-finance-browser.mjs` Balances section |
| FR-008 | US4 | `tests/finance/test_party_balances.py`, `tests/test_application_catalog.py`, capability guidance test |
| FR-009 | SC-004 | docs build, playbook text |
| DR-001–DR-004 | all | no migration in the diff; drill-down assertion in the browser suite |
