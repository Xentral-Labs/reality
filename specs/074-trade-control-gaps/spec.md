# Feature Specification: Overdue Payables

**Feature Branch**: `074-trade-control-gaps`
**Created**: 2026-09-04
**Status**: Draft
**Language**: English
**Input**: "Close the remaining trading control gap the current model can actually derive: a supplier invoice nobody paid."

## Context and Intent

### Problem

One condition a trading business cares about is derivable from records that already exist
and is not reported.

**Nobody sees an unpaid supplier invoice.** Spec 069 taught Reality when money is due and
used it on the customer side only, because dunning and paying are different decisions. The
consequence is one-sided: an overdue receivable appears, an overdue payable does not. A
supplier stops shipping, a discount lapses, a dunning fee arrives, and none of it was
visible in the queue that exists to say what needs attention. The rule, the derived due
date and the outstanding amount are all already there; only the payable half of the
open-item register is unread.

A second condition was specified beside it and then removed, because checking the model
showed it cannot occur. Goods moved beyond what a commitment promised looked like a gap —
every commitment class computes `max(0, promised − moved)` and the clamp appeared to hide
the opposite case. It hides nothing: `record_movement` refuses a movement beyond the
commitment's open quantity, no operation reduces a commitment's quantity afterwards, and a
correction carries no commitment reference at all. There is no path to an over-delivery, so
there is nothing to report.

### Scope

- Report a supplier invoice past its derived due date with an amount still outstanding.
- Reuse the existing due-date rule and the existing open-item derivation without adding a
  second copy of either.
- Give the class the identity, severity, impact, causal values, trace, explanation,
  ordering, tenant isolation and operator guidance every existing class carries.
- Extend the closed catalog and its drift gate.

### Non-Goals

- Anything that needs a link between an invoice and the order it invoices. Three further
  conditions were considered and are not in this feature — goods shipped but never
  invoiced, an invoice for goods never received, and a price that differs from the one
  agreed. The model has no document-to-document reference, invoices are never created from
  a source record, and matching by party and period would guess. That link is a schema
  question and belongs in its own specification.
- Negative stock. Every write path guards against it: outbound movements are refused beyond
  the stock at their location, and a correction is refused when later movements depend on
  the stock it would remove. A condition the product cannot reach is an engineering
  invariant, not an operator's decision. Stock that was negative at some past instant is a
  different, temporal question and is not addressed here either.
- Payment execution, dunning, or discount handling. The class reports the condition; paying is a separate decision.
- Goods moved beyond a commitment. The write path refuses it, no operation shrinks a
  commitment afterwards, and corrections carry no commitment reference, so the condition
  cannot arise.
- Under-delivery. While a commitment is open with quantity outstanding, that is precisely
  what the at-risk and overdue classes already report.
- Schema changes or migrations.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/069-overdue-receivables/spec.md`](../069-overdue-receivables/spec.md)
- [`specs/071-catalog-operator-guidance/spec.md`](../071-catalog-operator-guidance/spec.md)
- [`specs/008-commitments-holds/spec.md`](../008-commitments-holds/spec.md)
- [`specs/012-ledger-finance/spec.md`](../012-ledger-finance/spec.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-04

- Q: Why not the full three-way match between order, goods and invoice? → A: The model
  carries no reference from an invoice to the order it invoices, and invoices are never
  produced from a source record, so the two cannot be joined at all. Matching on party and
  period would produce an exception that is sometimes wrong, which is worse than none. The
  missing link is now justified by three concrete conditions and belongs in its own
  specification with its migration.
- Q: Why not negative stock? → A: It cannot happen. Outbound movements are refused beyond
  the stock at their location and corrections are refused when later movements depend on
  the stock they would remove, so a class for it would never fire in a correct system and
  would report an engineering fault rather than a business decision.
- Q: What happened to the over-delivery class? → A: Removed after checking the write path.
  `record_movement` refuses a movement beyond a commitment's open quantity, nothing reduces
  a commitment's quantity later, and a correction carries no commitment reference. It is the
  fourth condition in this line of work that the model prevents rather than tolerates, which
  is a finding about the product rather than a gap in it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the Supplier Invoices Nobody Paid (Priority: P1)

An operator sees every supplier invoice past the date its terms promised with money still
outstanding, alongside the customer invoices nobody paid, with the same meaning of "due".

**Why this priority**: It is the cheapest large gap left. The rule already exists and is
applied to one side only.

**Independent Test**: Post supplier invoices with terms of different lengths, some past due
and some not, settle some fully and some partially, then verify exactly the overdue
unsettled ones appear with the correct outstanding amount and days overdue.

**Acceptance Scenarios**:

1. **Given** a supplier invoice whose derived due date has passed and whose amount is not
   fully settled, **When** the queue is listed, **Then** one `overdue_payable` entry appears
   on that invoice with the outstanding amount, the due date and the days overdue.
2. **Given** the same invoice, **When** the outstanding amount is paid, **Then** the entry
   disappears without any manual step.
3. **Given** a supplier invoice whose payment term has not elapsed, **When** the queue is
   listed, **Then** no entry appears for it.
4. **Given** a customer invoice in the same state, **When** the queue is listed, **Then** it
   appears as an overdue receivable and not as an overdue payable.
5. **Given** a supplier invoice with no payment term whose supplier carries one, **When**
   the queue is listed, **Then** the supplier's term governs the due date, exactly as it
   does on the customer side.

### Edge Cases

- A supplier invoice is reversed, fully settled, or partly credited.
- A supplier invoice carries no readable document date.
- The identity of an entry is explained after the invoice was paid.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST report one `overdue_payable` entry for every supplier invoice
  whose derived due date precedes the evaluation instant and whose outstanding amount is
  above zero.
- **FR-002**: The derived due date and the outstanding amount for a payable MUST come from
  the same rule and the same derivation the receivable class uses, so the two sides cannot
  disagree about what "due" or "outstanding" means.
- **FR-003**: The system MUST NOT report a payable that is fully settled, reversed, not a
  supplier invoice, has no derivable due date, or is not yet due.
- **FR-004**: The entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace,
  in the same shape as every existing class.
- **FR-005**: The entry MUST disappear as soon as its condition ends — the payable settled
  or reversed — without acknowledgement or any other manual step.
- **FR-006**: The explanation of an entry MUST re-derive the current condition, and a
  malformed, unknown, cleared or foreign identity MUST produce the same not-found response
  the queue already returns.
- **FR-007**: The queue MUST remain deterministically ordered for identical data, with the
  longest-overdue payable first within its class.
- **FR-008**: The class MUST be declared in the closed catalog with an authority
  reference, named executable evidence, and the description, owner and clearing path every
  class carries, and any drift MUST fail the existing coverage gate.
- **FR-009**: Every surface that consumes the queue MUST receive the class through the
  existing shared list and explanation contract, without surface-specific derivation.

### Domain and Traceability Requirements

- **DR-001**: The class MUST be derived at read time from existing tenant-owned records.
  It adds no schema, no persisted state, and no status on any invoice.
- **DR-002**: The payable class MUST consume the existing aging register rather than
  deriving a due date of its own, so one rule still answers when money is due.
- **DR-003**: The trace MUST reach its records by opaque identity and MUST NOT restate
  business fields.
- **DR-004**: Every read, derivation and explanation MUST be tenant-scoped.
- **DR-005**: The class introduces no cause; the closed cause vocabulary is untouched.
- **DR-006**: The payable class and the receivable class, and the payable class and the
  overdue supplier delivery, are confusable pairs and MUST name each other, as Spec 071
  requires.

### Key Entities *(when data is involved)*

- **Document (supplier invoice)**: The evidence whose date and payment term decide when
  money is owed to a supplier.

## Success Criteria *(mandatory)*

- **SC-001**: An operator sees unpaid supplier invoices in the same queue and with the same
  meaning of "due" as unpaid customer invoices.
- **SC-003**: No due date and no outstanding amount is computed twice anywhere in the
  product as a result of this feature.
- **SC-004**: A settled payable leaves the queue on the next read with no manual action,
  and its former identity is no longer explainable.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- The payable side inherits every decision made for receivables in Spec 069: no grace
  period, the term cascading from the invoice to its party, and an unreadable invoice date
  asserting nothing.
- The class is severity `high`, consistent with every promise-related and financial
  class.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | overdue payable derivation test |
| FR-002 | US1 scenario 5 | shared aging rule test |
| FR-003 | US1 scenarios 3, 4; Edge cases | payable boundary test |
| FR-004 | US1 scenario 1 | entry shape and trace test |
| FR-005 | US1 scenario 2 | clearing through payment test |
| FR-006 | Edge cases | explanation not-found parity test |
| FR-007 | US1 scenario 1 | deterministic ordering test |
| FR-008 | US1 scenario 1 | catalog coverage and guidance gate test |
| FR-009 | US1 scenario 1 | shared list and explanation contract test |
| DR-001 | US1 scenario 2 | read-time derivation and no-persistence test |
| DR-002 | US1 scenario 5 | shared aging rule test |
| DR-003 | US1 scenario 1 | opaque trace test |
| DR-004 | Edge cases | tenant isolation test |
| DR-005 | US1 scenario 1 | existing cause-vocabulary drift gate |
| DR-006 | US1 scenario 4 | cross-reference review |
