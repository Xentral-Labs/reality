# Feature Specification: Overdue Receivable Visibility

**Feature Branch**: `069-overdue-receivables`
**Created**: 2026-09-04
**Status**: Draft
**Language**: English
**Input**: "Close the last large trading gap in the operational exception queue: a sales invoice that is past its due date with money still outstanding."

## Context and Intent

### Problem

A trading business fails on unpaid invoices before it fails on anything else, and Reality
cannot currently see one. The queue has a financial class, but
`unmatched_financial_event` requires a payment-side entry in the same posting group: it
finds money that arrived and could not be matched. An invoice that is weeks past its due
date and on which simply nothing arrived produces no entry at all. The most expensive
financial condition in the business is the one condition the decision queue is silent
about.

This is not a missing derivation. The arithmetic exists — twice. `aging_register` in
`services/core.py` derives a due date from the invoice date and the payment term and
counts days overdue, and `aging_page` in `web/read_models.py` computes the same thing
again line for line, including the same fallback and the same date-parsing guard. Neither
has a single caller anywhere in the repository. The rule was written, duplicated, and
wired to nothing, so the Open Items view shows open and settled amounts without ever
saying that an amount is late.

Two consequences follow. An operator has no way to learn from Reality that a customer has
not paid. And any third copy of that arithmetic — including one written for this feature —
would make three places that must agree about when money is due, which is precisely the
kind of divergence the queue must never have.

### Scope

- Report a sales invoice whose derived due date has passed while an amount remains
  outstanding, as its own exception class on the invoice.
- Derive the due date once, in the application layer, from invoice evidence and its
  payment term, and consume that one derivation from the queue.
- Make the duplicated copy in the read model use the shared derivation instead of its own
  arithmetic, so business rules leave the transport layer and cannot drift.
- Give the class the same identity, severity, impact, causal values, trace, explanation,
  ordering, and tenant isolation behavior as every existing class.
- Extend the closed catalog and its drift gate.

### Non-Goals

- Overdue payables. The condition is symmetric but the action is not: an unpaid customer
  invoice is dunned, an unpaid supplier invoice is paid. Each deserves its own entry and
  its own decision, and this feature delivers the receivable side only.
- Dunning levels, reminder letters, interest, credit limits, or any collection workflow.
- An aging report, aging buckets, or a due-date column anywhere in the interface. This
  feature wires the derivation to the queue, not to a new view.
- Configurable grace periods, tenant-specific severity, thresholds, notification, or
  escalation.
- Automatic remediation: writing off, rescheduling, or reversing anything.
- Persisted exception tickets, acknowledgement, assignment, or manual closure.
- New operational state on Documents. The invoice keeps its source lifecycle status only.
- Schema changes, migrations, or typed fields added for this derivation. Both inputs, the
  invoice date and the payment term, already exist.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/068-promise-coverage-exceptions/spec.md`](../068-promise-coverage-exceptions/spec.md)
- [`specs/020-exception-class-coverage/spec.md`](../020-exception-class-coverage/spec.md)
- [`specs/012-ledger-finance/spec.md`](../012-ledger-finance/spec.md)
- [`docs/features/ledger.md`](../../docs/features/ledger.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-04

- Q: Should the class cover payables as well? → A: No. Receivables only. The action
  differs — dunning against paying — and one entry must map to one decision. Payables are
  a named follow-up rather than a second half of this class.
- Q: What is the due date when an invoice has no payment term? → A: First accepted as the
  invoice date itself, inherited from both existing copies of the derivation. Revised the
  same day after measuring it: an imported ledger of 200 invoices produced 91 entries of
  which 20 were late only because no term applied, the youngest issued the day before. The
  term now cascades — the invoice's own term, else the party's, else the invoice date. Both
  dead copies were changed with it, so there is still one rule; inheriting a rule nobody
  had ever run was not worth a measured 22% false-positive rate.
- Q: Why is the party's term consulted at all? → A: Commercial terms are agreed with the
  customer, not restated on every invoice, and `Party.payment_term_id` already exists and
  is already maintained. An invoice is only due on issue when neither it nor its customer
  has a term.
- Q: Which record carries the exception? → A: The invoice Document. That is what an
  operator acts on and what the shared derivation is keyed to. The amount still comes
  from the ledger, and the control entry stays in the trace.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Which Customers Have Not Paid (Priority: P1)

An operator opens the decision queue and sees every sales invoice that is past its due
date with money still outstanding, with the outstanding amount and how long it has been
late, without opening a single invoice.

**Why this priority**: It is the only condition in this feature, and the largest remaining
blind spot in the queue for a trading business.

**Independent Test**: Issue sales invoices with payment terms of different lengths, some
past due and some not, settle some fully and some partially, then verify exactly the
overdue unsettled ones appear with the correct outstanding amount and days overdue.

**Acceptance Scenarios**:

1. **Given** a sales invoice whose derived due date has passed and whose amount is not
   fully settled, **When** the queue is listed, **Then** one `overdue_receivable` entry
   appears on that invoice with the outstanding amount, the due date, and the days
   overdue.
2. **Given** the same invoice, **When** the outstanding amount is settled — by a
   payment posted against it or by allocating a standalone payment to it — **Then** the
   entry disappears without any manual closure.
3. **Given** a partially settled overdue invoice, **When** the queue is listed, **Then**
   the entry reports the outstanding remainder and not the gross amount.
4. **Given** an invoice whose payment term has not yet elapsed, **When** the queue is
   listed, **Then** no entry appears for it.
5. **Given** an invoice with no payment term whose customer has one, **When** the queue is
   listed, **Then** the customer's term governs the due date, so a recently issued invoice
   does not appear.
5a. **Given** an invoice whose customer also has no term, **When** the invoice date has
   passed and the amount is outstanding, **Then** an entry appears, because nothing
   promises a later date.
6. **Given** an invoice whose recorded date is absent or unparseable, **When** the queue
   is listed, **Then** no entry appears for it, because no due date can be asserted.
7. **Given** a reversed invoice, **When** the queue is listed, **Then** no entry appears
   for it whatever its date.

### User Story 2 - One Rule About When Money Is Due (Priority: P2)

Whoever asks Reality when an invoice is due — the queue today, an aging view later — gets
the answer from one derivation, so two surfaces cannot disagree about the same invoice.

**Why this priority**: It is a prerequisite of User Story 1 rather than a smaller slice
of value. The class cannot be derived without this rule, and writing the rule twice is
what the story exists to prevent, so it lands first and is verified first. It carries P2
because on its own it changes nothing an operator can see.

**Independent Test**: Change the shared derivation and verify every consumer moves with
it; assert the read model performs no due-date arithmetic of its own. Verifiable before
the class exists, which is why it is sequenced ahead of it.

**Acceptance Scenarios**:

1. **Given** an invoice with a payment term, **When** the due date is requested through
   the queue and through the read model, **Then** both return the same date and the same
   days overdue for the same evaluation instant.
2. **Given** the read model, **When** it is inspected, **Then** it contains no due-date
   or aging arithmetic of its own.
3. **Given** an evaluation instant, **When** the queue is derived for it, **Then** the
   days overdue are counted against that instant and not against the wall clock.
4. **Given** an overdue receivable and an unmatched financial event of the same severity,
   **When** the queue is listed twice without changing data, **Then** both reads are
   identical and the overdue receivable is ordered first, longest overdue before the
   rest.

### Edge Cases

- An invoice is overdue on the day its term elapses, and one second before it.
- An invoice is fully settled, partially settled, unsettled, or reversed.
- A payment exists but is not allocated to the invoice, so nothing is settled.
- An invoice date is an empty string, a malformed string, or a valid date with no term.
- A payment term of zero days makes the invoice due on its own date.
- An invoice carries its own term while its party carries a different one.
- A party's term is changed after its invoices were issued, so their due dates move.
- A credit note reduces the outstanding amount to zero or below.
- Two tenants hold invoices with the same number and different opaque identities.
- The identity of an entry that has since been settled is submitted for explanation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST report one `overdue_receivable` entry for every sales
  invoice whose derived due date precedes the evaluation instant and whose outstanding
  amount is above zero.
- **FR-002**: The system MUST NOT report an entry when the outstanding amount is zero or
  below — a credit note that overpays an invoice therefore clears it — nor when the
  invoice is reversed, is not a sales invoice, has no derivable due date, or its due date
  has not passed.
- **FR-003**: The derived due date MUST be the invoice date advanced by the due days of
  the governing payment term. The governing term MUST be the invoice's own term where it
  has one, otherwise its party's term; only when neither exists is the invoice due on its
  own date. An invoice date that cannot be read yields no due date and therefore no entry.
- **FR-004**: The entry MUST report the outstanding amount rather than the gross amount,
  and MUST state the currency, the due date, and the days overdue at the evaluation
  instant.
- **FR-005**: The entry MUST carry a stable derived identity, severity, title, impact
  summary, authoritative record type and identity, causal values, and the shortest
  available Source → Evidence → Reality trace, in the same shape as every existing class.
- **FR-006**: The entry MUST disappear as soon as the invoice is settled or reversed,
  without acknowledgement, closure, or any other manual step.
- **FR-007**: The explanation of an entry MUST re-derive the current condition, and an
  identity that is malformed, unknown, settled, or owned by another tenant MUST produce
  the same not-found response the queue already returns.
- **FR-008**: The queue MUST remain deterministically ordered for identical data, with an
  overdue receivable ordered ahead of an unmatched financial event of the same severity.
- **FR-009**: One shared application derivation MUST answer when an invoice is due and how
  late it is, for a given evaluation instant. Every consumer MUST use it, and no transport
  or read model may compute a due date or an aging count of its own.
- **FR-010**: The class MUST be declared in the closed product catalog with an authority
  reference and named executable evidence, and any drift between the catalog, the
  derivations, and the declared order MUST fail the existing coverage gate.
- **FR-011**: Every surface that consumes the queue MUST receive the class through the
  existing shared list and explanation contract, without surface-specific derivation.

### Domain and Traceability Requirements

- **DR-001**: The class MUST be derived at read time from existing tenant-owned Document,
  PaymentTerm, LedgerEntry, and SettlementAllocation records. It adds no schema, no
  persisted exception state, and no operational state to the invoice.
- **DR-002**: The outstanding amount MUST come from the existing settlement derivation, so
  the queue, the open-item register, and the ledger cannot disagree about what an invoice
  still owes.
- **DR-003**: The trace MUST reach the invoice, its control ledger entry, and its
  SourceRecord by opaque identity, and MUST NOT restate their authoritative business
  fields.
- **DR-004**: The due-date rule MUST live in the application layer, not in a transport or
  read model, and MUST be reachable by every consumer through one name.
- **DR-005**: Every read, derivation, and explanation MUST be tenant-scoped, and no entry
  may reference a record outside its own tenant.
- **DR-006**: The class introduces no new cause. The outstanding remainder and the
  settlement status are causal values, not business reasons, so the closed cause
  vocabulary stays as it is.

### Key Entities *(when data is involved)*

- **Document (sales invoice)**: The evidence whose date and payment term decide when money
  is due, and the record an operator acts on. No new field is introduced.
- **PaymentTerm**: The due days that advance the invoice date. Optional, and its absence
  is meaningful rather than an error.
- **Outstanding amount**: The remainder derived from the control ledger entry and its
  settlement allocations; not a stored balance.
- **Exception class**: The catalog vocabulary that gains one class and no cause.

## Success Criteria *(mandatory)*

- **SC-001**: Every sales invoice past its due date with money outstanding is visible in
  the decision queue without opening a single invoice.
- **SC-002**: The queue and the read model return the same due date and the same days
  overdue for the same invoice and the same evaluation instant.
- **SC-003**: No due-date or aging arithmetic remains outside the application layer.
- **SC-004**: A settled or reversed invoice leaves the queue on the next read with no
  manual action, and its former identity is no longer explainable.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- Lateness is strictly a past due date at the evaluation instant, with no grace period,
  matching every existing overdue class. An invoice due exactly at the evaluation instant
  is not yet late.
- The governing term cascades from the invoice to its party. An invoice is due on its own
  date only when neither has a term, which keeps the fallback as a last resort rather than
  as the common case. Because a party's term is resolved at read time, changing it moves
  the due dates of its open invoices — that is intended: the queue reports current reality,
  not a snapshot taken at posting.
- Days overdue are counted in whole days between the due date and the evaluation instant.
- The outstanding amount, the settlement status, and the reversal state come from the
  existing open-item derivation; this feature adds no settlement behavior.
- Both dead copies of the aging arithmetic are treated as one rule to be consolidated, not
  as two features to be preserved. Wiring an aging view to that rule is explicitly out of
  scope and remains available afterwards.
- No payables condition is in scope. It stays a symmetric follow-up.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | overdue receivable derivation test |
| FR-002 | US1 scenarios 4, 6, 7 | settled, undue and reversed boundary test |
| FR-003 | US1 scenarios 5, 5a, 6; Edge cases | due-date derivation and term-cascade test |
| FR-004 | US1 scenarios 1, 3 | outstanding amount and aging test |
| FR-005 | US1 scenario 1 | entry shape and trace test |
| FR-006 | US1 scenario 2 | clearing through settlement test |
| FR-007 | Edge cases | explanation not-found parity test |
| FR-008 | US2 scenario 4 | deterministic ordering test |
| FR-009 | US2 scenarios 1, 2, 3 | single-derivation and read-model parity test |
| FR-010 | US1 scenario 1 | catalog coverage and drift gate test |
| FR-011 | US1 scenario 1 | shared list and explanation contract test |
| DR-001 | US1 scenario 2 | read-time derivation and no-persistence test |
| DR-002 | US1 scenario 3 | outstanding amount agreement test |
| DR-003 | US1 scenario 1 | opaque trace test |
| DR-004 | US2 scenario 2 | layering test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US1 scenario 1 | existing cause-vocabulary drift gate, guarding that no cause was added |
