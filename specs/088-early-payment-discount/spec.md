# Feature Specification: The Discount Nobody Is Watching

**Feature Branch**: `088-early-payment-discount`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "A payment term says only how many days. Every early-payment discount a company has negotiated is invisible to Reality — the ones it fails to take on the buying side, and the ones its customers take on the selling side, which leave a residue the queue reports as a debt forever."

## Context and Intent

### Problem

A `PaymentTerm` in Reality carries a code, a name and `due_days`. That is half of what a
payment condition actually says. The other half — "two per cent if you pay within ten days" —
is agreed constantly in trade and recorded nowhere, and its absence costs in two directions at
once.

**On the buying side, money is left on the table quietly.** A discount the company negotiated
expires by a date nobody is watching. Nothing in the product knows the offer exists, so nothing
can mention it while it is still there to take. It is the same shape as every other condition in
this queue: everything is recorded, everything is correct, and the loss happens because nobody
looked in time.

**On the selling side, the queue tells a lie.** A customer takes the discount it was offered and
pays 980 against a 1,000 invoice. Reality records the payment faithfully and the invoice stays
20 open — for ever. From its due date onward `overdue_receivable` reports it, every day,
alongside genuine debts. The customer did exactly what was agreed; the queue says they owe
money. That is a false positive in a shipped class, and on a business that grants discounts as a
matter of course there is one for every invoice it issues.

The second is a defect, not a gap. It is worth saying plainly: today, `overdue_receivable`
cannot be trusted by any company that grants an early-payment discount.

### Scope

- Let a payment term state the two figures that make an early-payment discount: a rate and a
  number of days. Both received, neither derived.
- One shared rule for the discount date, alongside the one due-date rule that already exists.
- Report an unpaid supplier invoice while its discount is still there to take.
- Say, on an overdue invoice whose remainder is no more than the agreed discount and whose
  payment arrived inside the window, that this is what happened — so an operator can settle the
  paperwork instead of chasing a customer who did nothing wrong.

### Non-Goals

- **Booking the discount.** Writing off the remainder to a discount account is bookkeeping, and
  Reality is not an accounting system. It reports that the residue is explained; recording the
  reduction is a credit note, which the product already has.
- **Computing any discount amount.** A rate applied to a gross amount is a division that
  produces money nobody agreed, with a remainder to round. No figure of that kind is ever
  reported or stored. The rate and the deadline are stated and reported as stated; the only
  money figure that appears is one the ledger already holds.
- **Deciding whether taking a discount is worth it.** Comparing a discount against the cost of
  money is a finance judgement, and it needs a cost of capital nobody has stated.
- **Suppressing the overdue entry.** The remainder genuinely is open. The entry stays and gains
  a reason; it does not disappear, because making a real balance invisible would be a worse lie
  than the one being fixed.
- **A discount that is not a payment term** — a negotiated one-off, a volume rebate, a
  settlement agreed on the telephone. Reality knows what a company wrote down.
- **Sliding scales.** "Three per cent in ten days, two per cent in twenty, net thirty" is one
  term with two windows. One window is recorded, and a company using two states the one it
  actually grants.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`docs/features/ledger.md`](../../docs/features/ledger.md)
- [`docs/features/master_data.md`](../../docs/features/master_data.md)
- [`specs/069-overdue-receivables/spec.md`](../069-overdue-receivables/spec.md)
- [`specs/084-credit-note-posts/spec.md`](../084-credit-note-posts/spec.md)
- [Constitution](../../.specify/memory/constitution.md), principles III and VIII

## Clarifications

### Session 2026-09-06

- Q: Is a rate not a licence to compute money? → A: It would be, and it is refused. A rate times
  a gross amount is a figure nobody agreed and it divides badly. The rate is used only on the
  comparing side of a comparison — is the unpaid remainder within what the agreed rate allows —
  and the figure the entry reports is the remainder the ledger already holds. Nothing is
  divided, nothing is rounded, and no money figure is authored.
- Q: Then why is the buying-side entry useful, if it cannot say how much? → A: Because it says
  the two things a company actually acts on: the rate it agreed and the date it expires. The
  amount follows from the invoice, which is on the same screen. Stating it would add nothing but
  a rounding decision.
- Q: Should the overdue entry disappear when the discount explains it? → A: No. Twenty is
  genuinely open on that invoice, and a queue that hides real balances is worse than one that
  explains them. The reason rides along as a cause, which is how this catalog already keeps one
  record from producing two rows.
- Q: What clears the buying-side entry? → A: Settling the invoice. It also stops appearing when
  the window closes, and that is the honest and uncomfortable half: this class goes quiet both
  when the discount is taken and when it is lost. Its own guidance says so, because an operator
  who does not know that will read silence as success.
- Q: Why not a class for a discount already lost? → A: Because nothing clears it. A lost
  discount is history, and every class in this catalog is a condition somebody can end. A
  permanent entry would be a report wearing a queue's clothes.
- Q: Which term applies to an invoice? → A: The one the aging register already uses — the
  invoice's own, else its party's, else none. There is one rule for that and this feature adds
  no second one.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Take the Discount While It Is There (Priority: P1)

An operator sees the supplier invoices where the company can still pay less, and by when.

**Why this priority**: It is the only moment at which anything can be done. A day later the
money is gone and no report brings it back.

**Independent Test**: Record a supplier invoice under a term granting a discount, leave it
unpaid, and read the queue inside and outside the window.

**Acceptance Scenarios**:

1. **Given** an unpaid supplier invoice under a term granting two per cent within ten days,
   **When** the queue is read on the fifth day, **Then** one entry appears naming the rate and
   the date the discount expires.
2. **Given** the same invoice settled, **When** the queue is read, **Then** nothing appears.
3. **Given** the same invoice unpaid on the eleventh day, **When** the queue is read, **Then**
   nothing appears, because there is nothing left to take.
4. **Given** a term that grants no discount, **When** the queue is read, **Then** nothing
   appears for any invoice under it.
5. **Given** several such invoices, **When** the queue is read, **Then** the one expiring
   soonest is first.

### User Story 2 - Stop Chasing a Customer Who Paid What Was Agreed (Priority: P1)

An overdue receivable whose remainder is the discount the customer was entitled to says so, so
an operator settles the paperwork rather than sending a reminder.

**Why this priority**: It is a false positive in a shipped class, and on a business granting
discounts routinely there is one for every invoice it issues.

**Acceptance Scenarios**:

1. **Given** a 1,000 invoice under two per cent within ten days, paid 980 on the fourth day,
   **When** the queue is read after the due date, **Then** the overdue entry appears carrying
   the reason that an early-payment discount was taken.
2. **Given** the same invoice paid 900 on the fourth day, **When** the queue is read after the
   due date, **Then** the overdue entry appears without that reason, because 100 is more than
   the agreed rate allows.
3. **Given** the same invoice paid 980 on the twentieth day, **When** the queue is read after
   the due date, **Then** the overdue entry appears without that reason, because the window had
   closed.
4. **Given** a credit note raised for the remainder and allocated, **When** the queue is read,
   **Then** no entry appears at all, because nothing is open.
5. **Given** an invoice nobody has paid at all, **When** the queue is read after the due date,
   **Then** the overdue entry appears without that reason.

### Edge Cases

- A term stating a rate and no days, or days and no rate.
- A rate of zero, and a rate of a hundred or more.
- An invoice with no readable date, so no window can be placed.
- A payment exactly on the last day of the window, and one exactly on the first day after.
- A remainder exactly equal to what the rate allows.
- An invoice settled by several payments, one inside the window and one outside.
- A supplier invoice and a customer invoice under the same term.
- A term changed after the invoice was issued.
- A term whose discount window outlasts its own due date.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A payment term MUST be able to state an early-payment discount rate and the number
  of days it is available for, and MUST keep working unchanged when it states neither.
- **FR-002**: A rate MUST be rejected unless it is above zero and below one hundred, and a
  number of discount days MUST be rejected unless it is zero or more.
- **FR-003**: A term stating only one of the two MUST be rejected, because half a discount
  condition is not a condition.
- **FR-004**: The discount deadline MUST be derived by one shared rule — the invoice's own date
  advanced by the stated discount days — used by everything that asks, so no two consumers can
  disagree about when a window closes.
- **FR-005**: The term governing an invoice MUST be the one the existing aging rule already
  resolves: the invoice's own, else its party's, else none.
- **FR-006**: No discount amount MUST be computed, reported or stored. A rate MUST be used only
  as one side of a comparison, and every money figure reported MUST be one the ledger already
  holds.
- **FR-007**: The system MUST report one entry per unpaid supplier invoice whose discount window
  is still open, stating the rate, the deadline and the amount outstanding.
- **FR-008**: That entry MUST disappear when the invoice is settled, and MUST stop appearing
  once the window has closed.
- **FR-009**: The guidance for that class MUST say plainly that it goes quiet both when the
  discount is taken and when it is lost, so that silence is not read as success. That MUST be
  proven by a test reading the guidance itself, because a gate that only checks guidance exists
  cannot check what it says.
- **FR-010**: An overdue invoice MUST carry a named reason when its unpaid remainder is no more
  than the agreed rate allows and the settled part arrived on or before the deadline.
- **FR-011**: That reason MUST NOT suppress or alter the entry in any other way. The outstanding
  amount reported MUST remain the amount that is genuinely open.
- **FR-012**: The reason MUST apply on both sides — a customer taking a discount and the company
  taking one from a supplier — because the condition is the same and the words differ.
- **FR-013**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace, in
  the same shape as every existing class.
- **FR-014**: The explanation of an entry MUST re-derive the current condition, and a malformed,
  unknown, cleared or foreign identity MUST produce the same not-found response the queue
  already returns.
- **FR-015**: The class and the cause MUST be declared in the closed catalog with an authority
  reference, named executable evidence, and the description, owner and clearing path every class
  carries.
- **FR-016**: Every surface that consumes the queue MUST receive the class and the cause through
  the existing shared list and explanation contract.
- **FR-017**: The queue MUST remain deterministically ordered for identical data.
- **FR-018**: Every surface that creates or updates a payment term MUST be able to state the two
  new figures, and MUST keep working unchanged when it states neither.

### Domain and Traceability Requirements

- **DR-001**: Two nullable columns on `payment_term`, added by one migration. Nullable is the
  statement: most terms grant no discount, and their absence says exactly that.
- **DR-002**: Both classes MUST be derived at read time from evidence the tenant already owns,
  and MUST store nothing.
- **DR-003**: One shared rule MUST answer when a discount window closes, in the same place as
  the one due-date rule, so the two cannot drift apart.
- **DR-004**: Traces MUST reach their records by opaque identity and MUST NOT restate business
  fields already carried in causal values.
- **DR-005**: Every read, derivation and explanation MUST be tenant-scoped.
- **DR-006**: One cause is added to the closed vocabulary, with the same authority and evidence
  a class requires.
- **DR-007**: No division MUST appear in any comparison this feature makes, so that no reported
  figure depends on a rounding decision.

### Key Entities *(when data is involved)*

- **PaymentTerm**: Gains the rate and the number of days an early-payment discount is available.
- **Document**: The invoice whose date places the window and whose amount is compared.
- **LedgerEntry** and **SettlementAllocation**: Say what was paid, and when.

## Success Criteria *(mandatory)*

- **SC-001**: A company can record the discount conditions it has actually negotiated.
- **SC-002**: An operator is told about a discount while it can still be taken, and told what it
  is not told when it can no longer be.
- **SC-003**: An overdue receivable explained by a discount the customer was entitled to says so
  and stops reading as a debt somebody must chase.
- **SC-004**: No money figure this feature reports is one that had to be rounded.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- One discount window per term. A sliding scale is a real thing in trade and is out; a company
  using one records the window it actually grants.
- The remainder test uses the invoice's gross amount, which is what a discount is agreed against
  in the ordinary case. Where a company grants it on the net amount instead, the comparison is
  slightly generous and will accept a remainder it should have queried. Being generous is the
  safe direction for a test whose purpose is to stop a false accusation.
- The buying-side class is silent for a company that records no discount terms, which is most of
  the world outside German-speaking trade. That is the honest shape of a feature built from what
  a company wrote down.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1, 4 | payment term discount test |
| FR-002 | Edge cases | rate and days validation test |
| FR-003 | Edge cases | half a condition test |
| FR-004 | US1 scenarios 1, 3 | shared discount date test |
| FR-005 | US1 scenario 1 | term resolution reuse test |
| FR-006 | US1 scenario 1; US2 scenario 1 | no authored amount test |
| FR-007 | US1 scenarios 1, 2 | discount available derivation test |
| FR-008 | US1 scenarios 2, 3 | clearing and window closing test |
| FR-009 | US1 scenario 3 | guidance content test |
| FR-010 | US2 scenarios 1, 2, 3, 5 | discount cause test |
| FR-011 | US2 scenario 1 | entry unchanged test |
| FR-012 | US2 scenario 1 | both sides test |
| FR-013 | US1 scenario 1; US2 scenario 1 | entry shape and trace test |
| FR-014 | Edge cases | explanation not-found parity test |
| FR-015 | US1 scenario 1 | catalog coverage and guidance gate test |
| FR-016 | US1 scenario 1 | shared list and explanation contract test |
| FR-017 | US1 scenario 5 | deterministic ordering test |
| FR-018 | US1 scenario 1 | adapter surface test |
| DR-001 | — | one migration adding two nullable columns |
| DR-002 | US1 scenario 2 | read-time derivation test |
| DR-003 | US1 scenario 3 | one shared window rule test |
| DR-004 | US1 scenario 1 | opaque trace test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US2 scenario 1 | cause vocabulary drift gate |
| DR-007 | US2 scenario 2 | no-division review and comparison test |
