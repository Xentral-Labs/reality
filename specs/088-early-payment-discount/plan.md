# Implementation Plan: The Discount Nobody Is Watching

**Branch**: `088-early-payment-discount` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Two nullable columns letting a payment term say what it has always said in the real world, one
shared rule for when the window closes, one class for a discount still available, and one cause
that stops a shipped class accusing customers who paid what was agreed.

The third schema change in this line of work, and the first that fixes a defect rather than
adding a capability.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; two nullable columns on `payment_term`, one revision
**Testing**: pytest business stories under `tests/operational_exceptions/` and the finance suite
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: Decimal money; no division anywhere in this feature; opaque IDs; strict tenant
scope
**Scale/Scope**: Two columns, one shared rule, one derivation, one cause, four adapter surfaces

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The rate and the days are Evidence a company recorded on its own payment term, alongside the days it already records. Every money figure reported comes from the ledger | PASS |
| Reality owns operational state | Nothing gains a status and nothing is booked; both entries are derived per read and stored nowhere | PASS |
| Proven schema only | Two nullable columns are what the feature cannot exist without: a rate and a window are not derivable from anything the model holds. Nullable is itself the statement that most terms grant no discount | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; the discount date joins the one due-date rule in the one aging register rather than being derived a second time | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | The available-discount entry names the rate, the deadline and the amount the ledger holds open. The cause names why a remainder is not a debt | PASS |
| Received values not recomputed | No discount amount is ever produced. The rate appears only on the comparing side of a comparison, multiplied out so that nothing is divided and nothing is rounded | PASS |
| Smallest coherent design | Four alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Compute and report the discount amount.** The obvious version and the one this product
  cannot have: two and a half per cent of 1,000.13 is a money figure nobody agreed, with a
  remainder to round. The rate and the deadline are what a company acts on, and the amount is on
  the same invoice.
- **Book the discount and close the invoice.** It would remove the residue entirely and it is
  bookkeeping — an amount written off to an account, authored by Reality. The residue is closed
  by a credit note, which spec 084 already built.
- **Suppress the overdue entry when a discount explains it.** Twenty is genuinely open. Hiding a
  real balance to avoid a false accusation trades one lie for a worse one; the entry stays and
  gains a reason, which is how this catalog already keeps one record from producing two rows.
- **A class for a discount already lost.** Nothing clears it. Every class here is a condition
  somebody can end, and a permanent entry is a report wearing a queue's clothes.

## Repository Structure and Layer Changes

```text
packages/reality-core/migrations/versions/0039_early_payment_discount.py  # two nullable columns
packages/reality-core/src/reality/db/core.py                     # the two columns
packages/reality-core/src/reality/services/core.py               # validation, the shared window rule, the aging row
packages/reality-core/src/reality/services/exceptions.py         # the class, the cause, registry, order
packages/reality-core/src/reality/catalogs.py                    # class order, cause vocabulary
packages/reality-core/config/operational_exception_catalog.yaml  # the class, the cause, guidance
packages/reality-core/config/command_catalog.yaml                # parameter descriptions
packages/reality-core/src/reality/web/api.py                     # request model and two endpoints
packages/reality-core/src/reality/mcp/catalog.py                 # two tool schemas
packages/reality-core/src/reality/cli/app.py                     # one command
docs/features/                                                    # operational exceptions, ledger, master data
apps/docs/content/catalogs/ (+ de/)                               # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                      # specification row
```

## Design

### The two columns

`discount_percent` as `Numeric(6, 3)` and `discount_days` as `Integer`, both nullable. Three
decimal places is past anything trade quotes — two and a half per cent, three, one and three
quarters — and a stored rate must never be a rounded version of the rate somebody stated.

Nullable is the statement. Most payment terms in most of the world grant no early-payment
discount, and a null says that exactly, without a zero that could be read as "nothing off"
rather than "no such offer".

Validation refuses the halves: a rate without days, or days without a rate. Half a discount
condition is not a condition, and accepting one would leave the derivations guessing which half
was meant.

### One rule for the window

`invoice_discount_date` sits beside `invoice_due_date`, takes the same document and the same
resolved term, and answers the same shape of question. The aging register enriches every row
with it, exactly as it already does with the due date — so the queue, the register and anything
else asking share one answer and cannot drift.

Which term governs an invoice is not re-decided. `effective_payment_term` already answers it —
the invoice's own, else its party's, else none — and this feature adds no second opinion.

### The class

`purchase_discount_available` walks the aging register for supplier invoices that are still
open, whose term states a discount, and whose deadline has not passed. It reports the rate, the
deadline, the days left and the amount the ledger holds open. It sorts on the deadline, so the
one about to expire is first, which is the only ordering an operator would want.

A term whose window outlasts its own due date is nonsense a company can nonetheless record,
and it produces both this entry and the overdue one on the same invoice. Nothing is done about
that: both statements are true, they are about different things, and inventing a precedence rule
for a condition nobody meant to create would be worse than the two rows.

**It goes quiet in two very different ways.** Settling the invoice ends it, and so does the
deadline passing. That asymmetry is uncomfortable and it is written into the class's own
guidance rather than left for somebody to discover: silence here means the discount was taken
*or* lost, and only the payment says which.

The alternative — a second class for a discount already lost — was rejected because nothing
clears it.

### The cause

`early_payment_discount_taken` rides on `overdue_receivable` and `overdue_payable` when three
things hold: the term states a discount, every settlement of that invoice arrived on or before
the deadline, and the unpaid remainder is no more than the rate allows.

The last of those is where the arithmetic could have gone wrong and does not. Instead of
producing an allowed amount and comparing against it, both sides are multiplied out:

```
remainder × 100  ≤  rate × gross
```

Nothing is divided, so nothing is rounded, and the only money figure the entry reports is the
remainder the ledger already holds. **DR-007 is the review test for this**: a division anywhere
in this feature is a defect regardless of what it produces.

Requiring *every* settlement to be inside the window is deliberate. An invoice paid in two
parts, one of them late, has not been settled early, and a discount claimed on it is exactly the
sort of thing an operator should still be looking at.

The comparison is made against the gross amount, which is what a discount is agreed against in
the ordinary case. Where a company grants it on the net amount instead, the test is slightly
generous and will accept a remainder it might have queried. That is the safe direction for a
test whose whole purpose is to stop a false accusation.

### Why the entry stays

Reality's job is to say what is true, and twenty is genuinely open on that invoice. What was
wrong was never the entry — it was that the entry gave no way to tell a customer who paid what
was agreed from one who has not paid. A cause is how this catalog already carries that
distinction, and it leaves the balance visible.

### Data and migration impact

One revision, `0039_early_payment_discount`, adding two nullable columns. No backfill: every
existing term keeps meaning exactly what it meant. Downgrade drops both.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_payment_terms.py::test_a_payment_term_can_state_a_discount` | the columns do not exist |
| FR-002 | service | `test_payment_terms.py::test_a_discount_rate_and_window_are_validated` | a nonsense rate is accepted |
| FR-003 | service | `test_a_discount_rate_and_window_are_validated` | half a condition is accepted |
| FR-004 | service | `test_payment_terms.py::test_the_discount_deadline_is_one_shared_rule` | consumers derive it separately |
| FR-005 | service | `test_the_discount_deadline_is_one_shared_rule` | a second term resolution appears |
| FR-006 | review + story | `test_derivation.py::test_no_discount_amount_is_ever_reported` | an authored amount appears |
| FR-007 | story | `test_derivation.py::test_purchase_discount_available` | class is not derived |
| FR-008 | story | `test_derivation.py::test_the_discount_entry_ends_both_ways` | it survives settlement or the deadline |
| FR-009 | unit | `test_coverage.py::test_the_discount_guidance_names_both_endings` | guidance omits the asymmetry |
| FR-010 | story | `test_derivation.py::test_a_discount_taken_explains_the_remainder` | the reason never appears |
| FR-011 | story | `test_a_discount_taken_explains_the_remainder` | the entry is suppressed or altered |
| FR-012 | story | `test_derivation.py::test_the_discount_reason_works_on_both_sides` | only one side carries it |
| FR-013 | service | `test_derivation.py::test_the_discount_entry_exposes_full_shape` | causal values missing |
| FR-014 | service | `test_explanation.py::test_discount_class_explanation_and_not_found_parity` | identity unknown to explanation |
| FR-015 | unit | `test_coverage.py` closed registry and cause tests | registry drift; missing guidance |
| FR-016 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| FR-017 | story | `test_derivation.py::test_the_discount_entry_orders_by_deadline` | order varies between reads |
| FR-018 | adapter | `test_api.py` and `test_application_catalog.py` surface tests | a surface cannot state the figures |
| DR-001 | review | exactly one file under `migrations/versions/` | — |
| DR-002 | story | `test_the_discount_entry_ends_both_ways` | something persists |
| DR-003 | service | `test_the_discount_deadline_is_one_shared_rule` | two rules appear |
| DR-004 | service | `test_the_discount_entry_exposes_full_shape` | trace restates business fields |
| DR-005 | story | `test_derivation.py::test_the_discount_class_is_tenant_scoped` | another tenant is read |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | the new cause is undeclared |
| DR-007 | review + unit | `test_derivation.py::test_nothing_in_this_feature_divides`, walking the syntax tree of the three functions for a division node | a division appears |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

One migration adding two nullable columns. Existing terms are untouched and every existing
behaviour is unchanged for them, so the deploy is invisible to a tenant that records no
discounts. Rollback drops the columns; nothing else depends on them.

The visible effects are both intended. A tenant that records discount terms gains a new queue of
supplier invoices it can still save money on, and its overdue receivables start explaining
themselves.

The demo month records no discount terms and will not change.

## Review Risks

- **A rate in the model is an invitation to compute with it.** Everything in this feature exists
  to make sure nobody does. The single guard is DR-007: no division. A reviewer should read the
  comparison and confirm that both sides are multiplied out, and treat any later division added
  near this code as a defect on sight.
- **The class goes quiet when the discount is lost.** This is the honest weakness of refusing to
  build a class that cannot clear, and it means silence carries two meanings. It is in the
  guidance, and a reviewer who thinks that is not enough is raising a fair point about FR-009
  rather than about the implementation.
- **Gross versus net is a real ambiguity and this feature picks one.** The comparison is
  generous where a company discounts the net amount, which means a remainder it should have
  queried can be accepted as explained. Being generous is the safe direction here and it is
  still a case where the queue says less than it might.
- **The cause changes what a shipped class means.** `overdue_receivable` will start carrying a
  reason on entries that previously carried none. Nothing is suppressed and no figure moves, and
  the existing suites passing untouched is the evidence for that.
- **Two figures on a payment term reach four adapters.** The risk is not the columns but a
  surface silently unable to state them, which is why FR-018 is a requirement with its own test
  rather than a cleanup task.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| Schema change: two nullable columns on `payment_term` | An early-payment discount is a rate and a window, and neither is derivable from anything the model holds. Without them the buying side is blind and the receivable queue keeps accusing customers who paid what was agreed | Inferring a discount from short payments — a guess wearing arithmetic, and it would explain a genuine underpayment as readily as a real discount | Recorded here; the migration is one revision with no backfill |
