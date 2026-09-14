# Feature Specification: One Friday, Forty Payments

**Feature Branch**: `098-a-payment-run`
**Created**: 2026-09-07
**Status**: Draft
**Language**: English
**Input**: "Der Zahllauf. `post_supplier_payment` nimmt genau eine `invoice_id`, und die Guidance von `purchase_discount_available` verweist selbst auf einen Zahllauf, den es nicht gibt."

## Context and Intent

### Problem

A company pays its suppliers on a day, not one at a time. `post_supplier_payment` takes exactly
one `invoice_id` and one amount. So the ordinary Friday afternoon is forty separate operations,
and three things are wrong with that:

**Nothing records that they were one decision.** Forty payments went out because one person
looked at what was due and said yes once. Reality keeps forty unrelated postings and no trace of
the decision above them, so nobody can later ask what that Friday's run consisted of, who
approved it, or why.

**A run can half-happen.** The twentieth invoice turns out to have been paid already, or a
document is not what it claims to be, and the operation raises. Nineteen payments stand, twenty
do not, and the person has to work out which. There is no operation in the product that says
*these payments happened together or none of them did.*

**Nothing tells you what is worth paying now.** The information exists — `aging_register` knows
what is open and when it is due, `purchase_discount_available` knows which invoices can still be
paid for less — but there is no read that assembles it into *what should go out on Friday*. The
discount class's own guidance names its owner as "Accounts payable, with whoever schedules the
payment run", which is a role the product does not support.

### Scope

- One read that says what is worth paying now, and writes nothing.
- One operation that pays what a person confirmed, in a single transaction.
- One record that those payments were one decision, with the reason kept.

### Non-Goals

- **Computing what to pay.** This is the whole shape of the feature. Every amount in a run is an
  amount somebody stated. Reality never multiplies a gross amount by a discount rate, because
  that is a division producing money nobody agreed to, with a remainder to round. The preview
  names what is open and names the rate the company negotiated; the decision to pay 98 instead
  of 100 is a person's, and the 98 is a received value like every other.
- **A bank file, a payment method, or anything that leaves the building.** A run records that
  the company paid. How the money moves is not in this product and this specification does not
  pretend it is.
- **Writing off the residue of a discount taken.** Paying 98 of 100 leaves 2 open. That already
  shows as Overdue payable with the early-payment-discount reason, which the catalog already
  describes. Clearing it is a separate act and this run does not invent one.
- **Deciding whether to pay.** A run pays what it was told to pay. Which invoices belong in it is
  a commercial judgement with a person behind it — the preview is an argument, not an instruction.
- **A per-invoice payment block.** Excluding an invoice from a run means not naming it. There is
  no durable "do not pay this one" marker, so an invoice held back reappears in next week's
  preview. That is correct — an unpaid invoice under dispute *should* keep being reported — but
  it is a real cost and it is named here rather than hidden.
- **Paying anything but supplier invoices.** A credit note is netted, a refund is taken back, and
  both already have their operation.

### Existing Contracts

- [`specs/085-close-stale-promises/spec.md`](../085-close-stale-promises/spec.md) — the preview,
  confirm and single-transaction shape this follows
- [`specs/088-early-payment-discount/spec.md`](../088-early-payment-discount/spec.md)
- [`docs/features/procure_to_pay.md`](../../docs/features/procure_to_pay.md)
- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [Constitution](../../.specify/memory/constitution.md), principles I and VIII

## Clarifications

### Session 2026-09-07

- Q: Does the run work out what to pay, the way an ERP payment run does? → A: No, and this is the
  central decision. It pays amounts somebody stated. A rate applied to a gross amount is exactly
  the computation Principle VIII forbids, and a payment run is where an ERP does the most of it.
- Q: Which invoices belong in a run that is being made for a particular day? → A: Those due on
  or before it, and those whose early-payment window has not closed yet — measured against today
  rather than against the stated day, because an invoice whose window shuts tomorrow is the most
  urgent thing on the list, not the least.
- Q: Then what does the preview do, if it does not compute? → A: It assembles what is already
  derived — what is open, when it is due, whether a discount window is still open and at what
  rate — and orders it. Every figure in the preview comes from `aging_register`, which is where
  those figures already live.
- Q: Does the run derive which invoices to pay? → A: No. The caller names them. A derived
  selection would mean the run pays something nobody looked at, and the whole point of the
  preview-and-confirm shape is that a person looked.
- Q: Then what stops a run paying something it should not? → A: The run refuses anything the
  preview would not have proposed: a document that is not a supplier invoice, one whose posting
  has been reversed, one with nothing open, one already reported as a duplicate, and any amount
  above what is open. One rule decides what is payable, and both the preview and the run ask it.
- Q: Why refuse a duplicate outright, when this queue reports rather than refuses? → A: Because
  paying it is unrecoverable and the class is the one payable condition marked high. It has a
  clearing path — reverse the wrong posting, or confirm the numbers differ — so refusing does not
  trap anybody.
- Q: What confirmation figure does a run need? → A: The total. Spec 085 confirmed a count because
  a count was what the person saw. Here the person approves an amount of money, and a list built
  by a client from a preview can be right in every line and wrong in sum.
- Q: Can one run pay in two currencies? → A: No. A total in two currencies is not a total, and
  converting would guess — the same rule Spec 076 applied to units and Spec 078 to credit limits.
- Q: What happens if one payment in a run fails? → A: None of them happened. That is the reason
  the operation exists.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - What Should Go Out On Friday (Priority: P1)

An operator asks what is worth paying, gets an ordered answer with nothing changed, and can see
at a glance which invoices are simply due and which are still inside a discount window.

**Why this priority**: Without it the run is a list somebody has to assemble by hand from a
register and a queue, which is the work the product is supposed to do.

**Independent Test**: Record four supplier invoices with different due dates and terms, ask for
the preview, and read it.

**Acceptance Scenarios**:

1. **Given** four open supplier invoices, **When** the preview is asked for what is due before a
   date, **Then** it names those that are, with what each has open, ordered by the day the money
   is needed and then by identity.
2. **Given** an invoice inside its discount window but not yet due, **When** the preview is
   asked, **Then** it is included and names the rate and the day the window closes.
3. **Given** the preview, **When** the tenant is read again, **Then** nothing has changed: no
   document, no posting, no event.
4. **Given** invoices from three suppliers, **When** the preview is read, **Then** it says what
   each supplier is owed as well as what the run totals.
5. **Given** an invoice reported as a duplicate, one whose posting was reversed, and one already
   settled, **When** the preview is asked, **Then** none of them is proposed and each is named as
   withheld with the reason.

### User Story 2 - Forty Payments, One Decision (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a confirmed list of invoices and amounts and a matching total, **When** the run is
   executed, **Then** every payment is posted, every invoice is settled by it, and one event
   records the run with its reason and every invoice in it.
2. **Given** the same list where one invoice was settled by somebody else in between, **When**
   the run is executed, **Then** it is refused and **nothing at all** has been posted.
3. **Given** a list whose amounts do not sum to the confirmed total, **When** the run is
   executed, **Then** it is refused.
4. **Given** a run, **When** the ledger is read, **Then** each payment stands on its own — the
   run is a record of a decision, not a document anything is posted against.

### User Story 3 - The Discount Is Named, Never Applied (Priority: P1)

**Acceptance Scenarios**:

1. **Given** an invoice of 100 with a 2% term still inside its window, **When** the preview is
   read, **Then** it names 100 open, 2% and the deadline, and **states no discounted amount**.
2. **Given** the operator states 98, **When** the run is executed, **Then** 98 is paid and 2
   stays open on the invoice.
3. **Given** that residue, **When** the queue is read, **Then** the invoice appears as an overdue
   payable with the early-payment-discount reason, exactly as it does after a single payment.

### Edge Cases

- A run naming the same invoice twice.
- A run naming invoices in two currencies.
- An amount above what the invoice has open.
- An empty run.
- A run with no reason.
- A run on a tenant whose invoice belongs to another tenant.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: One rule MUST decide whether a supplier invoice is payable, and both the preview
  and the run MUST ask it. Nothing else may decide it.
- **FR-002**: An invoice MUST NOT be payable when it is not a supplier invoice, when its posting
  has been reversed, when it has nothing open, or when it is reported as a duplicate supplier
  invoice.
- **FR-003**: The preview MUST write nothing — no document, no posting, no event, no projection.
- **FR-004**: The preview MUST propose every payable invoice due on or before a stated day, and
  every payable invoice whose early-payment window has not yet closed, ordered by the day the
  money is needed — an open discount deadline where there is one, the due date otherwise — and
  then by identity.
- **FR-005**: The preview MUST name, per invoice, what is open, the day it is due, and — where a
  term states one — the rate and the day the window closes. It MUST NOT name a discounted amount.
- **FR-006**: The preview MUST say what it withheld and why.
- **FR-007**: The preview MUST report what each supplier is owed as well as the run's total.
- **FR-008**: The run MUST pay exactly the invoices and amounts it was given; it MUST derive no
  amount and select no invoice of its own.
- **FR-009**: The run MUST refuse an invoice that is not payable, an amount above what an invoice
  has open, an invoice named twice, an empty list, a run without a stated reason, and a run whose
  amounts do not sum to the confirmed total.
- **FR-010**: A run MUST be in one currency, and the confirmed total MUST be stated in it.
- **FR-011**: The run MUST post every payment in one transaction: either every payment and its
  settlement stands, or nothing at all does.
- **FR-012**: The run MUST record one business event naming the reason, the total, the currency
  and every invoice with the amount paid against it.
- **FR-013**: Every payment in a run MUST be indistinguishable in the ledger from the same
  payment made on its own.
- **FR-014**: The discount class's guidance MUST name the operation that now exists.
- **FR-015**: Every existing class, operation and register MUST behave exactly as it does today.

### Domain and Traceability Requirements

- **DR-001**: No migration. Every figure and relation this needs already exists.
- **DR-002**: The payable rule MUST reuse the duplicate-invoice rule rather than restate it, and
  that rule MUST live in one place with the exception class as its other consumer.
- **DR-003**: Every figure the preview reports MUST come from `aging_register`, so the preview,
  the register and the queue can never disagree.
- **DR-004**: Every read, derivation and write MUST be tenant-scoped.
- **DR-005**: No operational exception class or cause is added.
- **DR-006**: Every amount paid MUST be one somebody stated; none may be derived, rounded or
  adjusted.
- **DR-007**: Both operations MUST be declared commands, so the reachability gate stays satisfied.

### Key Entities *(when data is involved)*

- **Document**: The supplier invoices a run pays and the supplier payments it creates. A run
  itself is not a document — it is a decision, and it is recorded as an event.
- **LedgerEntry** and **SettlementAllocation**: unchanged, one pair per payment, exactly as a
  single payment produces.
- **BusinessEvent**: the one record that these payments were one decision.

## Success Criteria *(mandatory)*

- **SC-001**: A person can see what is worth paying without assembling it from two screens.
- **SC-002**: A run either happened or did not; there is no partial Friday.
- **SC-003**: Reality states no amount of money that nobody agreed to.
- **SC-004**: What a run consisted of, and why, can be read back afterwards.
- **SC-005**: A payment made in a run is the same posting as a payment made alone.
- **SC-006**: Two identical previews of an unchanged tenant return an identical, identically
  ordered answer.
- **SC-007**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- An invoice held back from a run reappears in the next preview. There is no durable per-invoice
  block, and that is a stated limit of this feature.
- The residue left by taking a discount stays open and is reported, not cleared. Spec 088 already
  decided that and this does not revisit it.
- Reality does not move money. A run records that a company paid; the transfer happens elsewhere
  and the product does not claim otherwise.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 5; US2 scenario 2 | one payable rule test |
| FR-002 | US1 scenario 5 | withheld reasons test |
| FR-003 | US1 scenario 3 | preview writes nothing test |
| FR-004 | US1 scenarios 1, 2 | preview selection and order test |
| FR-005 | US3 scenario 1 | discount named, not applied test |
| FR-006 | US1 scenario 5 | withheld reasons test |
| FR-007 | US1 scenario 4 | per-supplier totals test |
| FR-008 | US2 scenario 1 | stated amounts test |
| FR-009 | US2 scenarios 2, 3; Edge cases | refusals test with positive controls |
| FR-010 | Edge cases | mixed-currency refusal test |
| FR-011 | US2 scenario 2 | all-or-nothing test |
| FR-012 | US2 scenario 1 | run event test |
| FR-013 | US2 scenario 4; US3 scenario 2 | ledger parity test |
| FR-014 | — | catalog guidance and drift gates |
| FR-015 | — | the existing suites, unchanged |
| DR-001 | — | no migration added |
| DR-002 | US1 scenario 5 | shared duplicate rule test |
| DR-003 | US3 scenario 1 | figures come from the register test |
| DR-004 | Edge cases | tenant isolation test |
| DR-005 | — | the closed registry expectation, unchanged |
| DR-006 | US3 scenarios 1, 2 | recorded-amounts-only test |
| DR-007 | — | the command reachability gate |
