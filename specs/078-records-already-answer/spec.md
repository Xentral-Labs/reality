# Feature Specification: Two Answers the Records Already Hold

**Feature Branch**: `078-records-already-answer`
**Created**: 2026-09-05
**Status**: Draft
**Language**: English
**Input**: "Collect the exception classes a B2C and B2B trading business needs across order-to-cash, procure-to-pay and return-to-resolution, then build what is missing."

## Context and Intent

### Problem

Two conditions a trading business acts on every week are already answerable from records
Reality holds today. Neither needs a column, an edge, or a rule about time. Both are simply
never asked.

**A customer owes more than the company agreed to carry.** `party.credit_limit` has existed
since the master-data baseline. It is validated on write, carried through updates, and
included in the audit trail. Nothing reads it. The outstanding amount to compare it against
is already derived — `financial_open_items` produces every open invoice with its party and
its remaining balance, and the receivable and payable classes both consume it. The two
halves of the comparison sit in the same process and have never been put together.

**The same supplier invoice is recorded twice.** `document` is unique on
`(tenant_id, source_record_id, type)`, which stops one source record producing two
documents. It says nothing about two source records carrying the same invoice, and nothing
at all about manual entry: recording invoice `ER-4711` from Bike Parts GmbH twice succeeds
today, and produces two payables, two postings and two amounts to pay.

That second case is not an accident of the model but a consequence of a principle. Reality
records what a source states and judges afterwards; refusing the second document would
discard evidence that a source really did send it. What is missing is the judgement, not
the refusal.

### Scope

- Report a Party whose outstanding receivables exceed the credit limit recorded on it.
- Report a supplier invoice whose number and Party match one already recorded.
- Give both the identity, severity, impact, causal values, trace, explanation, ordering,
  tenant isolation and operator guidance every existing class carries.

### Non-Goals

- Enforcing either condition. Reality reports; blocking a delivery is `party_delivery_hold`,
  an explicit operation a person takes. Neither class refuses anything.
- Exposure beyond invoiced amounts. Unshipped orders and undelivered promises are a larger
  and separate question about what a credit limit is measured against; this feature compares
  the limit with money actually owed.
- Currency conversion. A limit is one number and a Party has one default currency; open
  items in another currency are not converted into it.
- Duplicate detection by content. Two invoices with different numbers that happen to carry
  the same lines and amount are not compared. Matching a number is a statement both
  documents make about themselves; matching content is a guess.
- Sales invoice numbering. A duplicate number the company issued itself is a different
  problem with a different owner and no money at risk.
- Any change to the write path. Both documents stay recorded, both postings stay posted.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/004-master-data/spec.md`](../004-master-data/spec.md)
- [`specs/012-ledger-finance/spec.md`](../012-ledger-finance/spec.md)
- [`specs/069-overdue-receivables/spec.md`](../069-overdue-receivables/spec.md)
- [`specs/071-catalog-operator-guidance/spec.md`](../071-catalog-operator-guidance/spec.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-05

- Q: `credit_limit` defaults to zero. Does a customer with no limit set have a limit of
  nothing? → A: No, and reading it that way would report every customer with a single open
  invoice on the day the class ships. Zero means no limit is recorded, and a Party with no
  recorded limit is never reported. Only a limit above zero is a limit.
- Q: What counts against the limit? → A: Money actually owed — the outstanding balance of
  open sales invoices, taken from the same derivation the receivable class uses. Unshipped
  orders are exposure too, and including them would change what the number means; that is a
  separate decision, recorded here as a non-goal rather than made quietly.
- Q: A Party's open items are in two currencies. What is compared? → A: Only the items in
  the Party's own default currency. This is the same rule Spec 076 applied to units: a
  converted figure would be a guess and an unconverted one would be wrong. If the excess
  exists only outside that currency, nothing is reported.
- Q: Should a duplicate supplier invoice be refused at write time instead? → A: No. Reality
  records losslessly and judges afterwards, and the same invoice legitimately arrives twice
  when two connectors carry it. Refusing would destroy the evidence that both arrived. The
  class names the later document and points at the earlier one.
- Q: Do `ER-4711` and `er-4711 ` match? → A: Yes. Numbers are compared with surrounding
  whitespace removed and case ignored. A supplier that deliberately issues both is
  imaginable and has never been seen; a missed duplicate costs a payment, a false one costs
  an operator a glance.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See a Customer Past the Limit Agreed With Them (Priority: P1)

An operator sees customers whose unpaid invoices exceed the credit limit recorded on them,
with the limit, the outstanding amount and the excess.

**Why this priority**: It is the oldest control in B2B trade, the field has been carried for
this purpose since the beginning, and nothing has ever read it.

**Independent Test**: Record a customer with a limit, invoice beyond it, verify the excess
is reported; settle enough to fall under the limit and verify it clears.

**Acceptance Scenarios**:

1. **Given** a customer with a recorded limit and open invoices above it, **When** the queue
   is listed, **Then** one entry appears with the limit, the outstanding amount and the
   excess.
2. **Given** the same customer, **When** enough is paid to fall under the limit, **Then**
   the entry disappears without any manual step.
3. **Given** a customer with no recorded limit, **When** the queue is listed, **Then** no
   entry appears, whatever is outstanding.
4. **Given** a customer exactly at the limit, **When** the queue is listed, **Then** no
   entry appears, because the agreed amount is allowed.
5. **Given** a customer whose excess exists only in a currency other than their own,
   **When** the queue is listed, **Then** no entry appears.

### User Story 2 - See the Same Supplier Invoice Twice (Priority: P1)

An operator sees a supplier invoice recorded under a number that supplier already used, with
both documents named.

**Why this priority**: It is money leaving twice for one delivery, and nothing in the write
path prevents it.

**Independent Test**: Record two supplier invoices with the same number and Party, verify the
later one is reported and names the earlier.

**Acceptance Scenarios**:

1. **Given** two supplier invoices with the same Party and number, **When** the queue is
   listed, **Then** one entry appears on the later document, naming the earlier.
2. **Given** three such invoices, **When** the queue is listed, **Then** two entries appear,
   each naming the first.
3. **Given** two invoices with the same number from different suppliers, **When** the queue
   is listed, **Then** no entry appears, because a number is only unique within the supplier
   that issued it.
4. **Given** numbers differing only in case or surrounding whitespace, **When** the queue is
   listed, **Then** they are treated as the same number.
5. **Given** a supplier invoice with no number at all, **When** the queue is listed, **Then**
   it is never reported and never matched against.

### Edge Cases

- A Party that is both customer and supplier.
- A credit limit recorded and later removed.
- An outstanding balance that is negative because a credit note exceeds the invoice. The
  write path already refuses this: crediting more than the open receivable is rejected where
  the credit is posted, so the sum cannot go negative from that direction.
- A reversed invoice that no longer counts as outstanding.
- Two duplicate invoices recorded in the same second, so neither is obviously later.
- A duplicate where one document has been reversed, and a supplier reissuing a corrected
  invoice under the same number.
- A duplicate discovered before either invoice is posted, which is the case worth catching
  earliest and the one an open-item derivation would never see.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST report one entry for every Party whose outstanding receivables
  exceed the credit limit recorded on that Party. Only sales invoices count: what a Party is
  owed by the company is not what the company agreed to let it owe, so a Party that is both
  customer and supplier is judged on its customer side alone.
- **FR-002**: A credit limit of zero MUST mean that no limit is recorded, and such a Party
  MUST NOT be reported.
- **FR-003**: Outstanding receivables MUST come from the existing open-item derivation, so
  the figure can never disagree with the receivable class or the aging register. That
  derivation already reports a reversed invoice as nothing outstanding and a settled one as
  zero; neither is re-decided here.
- **FR-004**: Only open items in the Party's own default currency MUST be counted, and a
  Party MUST NOT be reported on the strength of items in another currency.
- **FR-005**: An outstanding amount equal to the limit MUST NOT be reported.
- **FR-006**: The system MUST report one entry for every supplier invoice whose Party and
  number match an earlier supplier invoice of the same tenant.
- **FR-007**: Numbers MUST be compared with surrounding whitespace removed and case ignored,
  and a document with an empty number MUST neither be reported nor matched against.
- **FR-008**: The earlier document MUST be identified deterministically, so that repeated
  reads name the same document as the original.
- **FR-008a**: A supplier invoice whose posting has been reversed MUST be neither reported
  as a duplicate nor matched against, because a withdrawn invoice is not one the company can
  pay twice — and a supplier reissuing a corrected invoice under its original number is
  ordinary rather than a finding.
- **FR-009**: Each entry MUST state the two figures or documents it compares.
- **FR-010**: Each entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace,
  in the same shape as every existing class.
- **FR-011**: Each entry MUST disappear as soon as its condition ends, without
  acknowledgement or any other manual step.
- **FR-012**: The explanation of an entry MUST re-derive the current condition, and a
  malformed, unknown, cleared or foreign identity MUST produce the same not-found response
  the queue already returns.
- **FR-013**: Both classes MUST be declared in the closed catalog with an authority
  reference, named executable evidence, and the description, owner and clearing path every
  class carries.
- **FR-014**: Every surface that consumes the queue MUST receive both classes through the
  existing shared list and explanation contract.
- **FR-015**: The queue MUST remain deterministically ordered for identical data.

### Domain and Traceability Requirements

- **DR-001**: Neither class writes anything. Both are read-time observations over Parties,
  Documents and the existing settlement derivation.
- **DR-002**: The outstanding amount MUST NOT be recomputed from postings. It is the figure
  the shared open-item derivation already produces, which Constitution principle VIII
  requires and which keeps every consumer agreeing.
- **DR-003**: `party` becomes the ninth authoritative record type; the duplicate class is
  carried by `document`, which already exists.
- **DR-004**: Traces MUST reach their records by opaque identity and MUST NOT restate
  business fields.
- **DR-005**: Every read, derivation and explanation MUST be tenant-scoped.
- **DR-006**: No cause is introduced; the closed cause vocabulary is untouched.
- **DR-007**: No schema changes. Both conditions are answerable from records that exist.

### Key Entities *(when data is involved)*

- **Party**: Carries the credit limit and the default currency it is expressed in.
- **Document**: The supplier invoices whose numbers are compared, and the sales invoices
  whose outstanding balances are summed.

## Success Criteria *(mandatory)*

- **SC-001**: A field carried since the master-data baseline is read for the first time.
- **SC-002**: An operator is told before paying, not after, that an invoice number has been
  seen before from that supplier.
- **SC-003**: The outstanding amount an operator reads here is the same number the aging
  register and the receivable class show.
- **SC-004**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-005**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- A recorded credit limit means the company agreed to carry that much. Reality does not ask
  how the figure was arrived at and does not maintain it.
- Comparing money owed rather than total exposure is the smaller and more defensible of two
  readings. It will understate risk for a business with large unshipped order books, and
  that is named as a non-goal rather than hidden.
- Supplier invoice numbers are issued by the supplier and unique within it. That is the
  assumption the duplicate class rests on; a supplier that reuses numbers across years would
  produce a false entry, which an operator resolves by looking at two documents.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | credit exposure derivation test |
| FR-002 | US1 scenario 3 | absent-limit test |
| FR-003 | US1 scenario 1 | shared open-item path test |
| FR-004 | US1 scenario 5 | foreign-currency test |
| FR-005 | US1 scenario 4 | exactly-at-limit test |
| FR-006 | US2 scenarios 1, 2 | duplicate derivation test |
| FR-007 | US2 scenarios 4, 5 | number normalisation test |
| FR-008 | US2 scenario 2 | deterministic original test |
| FR-008a | Edge cases | reversed-duplicate test |
| FR-009 | US1 scenario 1; US2 scenario 1 | causal values test |
| FR-010 | US1 scenario 1 | entry shape and trace test |
| FR-011 | US1 scenario 2 | clearing test per class |
| FR-012 | Edge cases | explanation not-found parity test |
| FR-013 | US1 scenario 1 | catalog coverage and guidance gate test |
| FR-014 | US1 scenario 1 | shared list and explanation contract test |
| FR-015 | US2 scenario 2 | deterministic ordering test |
| DR-001 | US1 scenario 2 | read-time derivation test |
| DR-002 | US1 scenario 1 | shared open-item path test |
| DR-003 | US1 scenario 1 | record type test |
| DR-004 | US1 scenario 1 | opaque trace test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US1 scenario 1 | existing cause-vocabulary drift gate |
| DR-007 | — | no migration added |
