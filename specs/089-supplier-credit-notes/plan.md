# Implementation Plan: The Credit That Comes the Other Way

**Branch**: `089-supplier-credit-notes` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Spec 084 in the other direction: a supplier credit note that posts as the reverse of a supplier
invoice, nets against a payable or is refunded, and two classes for the credits nobody booked
and nobody claimed.

No schema. Four settleable documents become six, and the settlement relation that already links
any two control entries on opposite sides of one account does the rest.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalogs
**Storage**: PostgreSQL; no schema change
**Testing**: pytest business stories under `tests/` and `tests/operational_exceptions/`
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: Decimal money; posted amounts equal recorded amounts; opaque IDs; tenant scope
**Scale/Scope**: Four operations, two rows in one table, two classes

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The credit note is Evidence a supplier sent; the postings carry its own gross amount and nothing else | PASS |
| Reality owns operational state | Both classes are derived per read; settlement state is the existing allocation relation, not a status | PASS |
| Proven schema only | No schema change. A Document type is already a free string and the settlement relation is already general | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; settlement goes through the one existing allocation service, so no second way of reducing a payable appears | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Each entry names the amount, the supplier and how long it has stood, and traces to the document by identity | PASS |
| Received values not recomputed | Every posted figure is the credit note's own gross amount. Nothing is apportioned, split or rounded. The learned threshold is an observation over this tenant's own history, stored nowhere | PASS |
| Smallest coherent design | Three alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **One credit note type for both directions, with the party deciding the posting.** Fewer
  strings and a worse model: the two are settled against different control accounts, owned by
  different people, and cleared by different actions. The type is what makes a document's
  postings knowable without inspecting its party.
- **One class covering credits in both directions.** The condition looks identical and the job
  is not. A credit the company owes is settled by its own accounts receivable; a credit a
  supplier owes is claimed from that supplier by accounts payable. One row for two jobs is a
  worklist nobody owns.
- **Wait for the goods half.** A supplier return cannot be recorded at all today, so a credit
  for returned goods has no movement behind it. Waiting would also withhold the credits that
  never had goods behind them — a price correction, an allowance, a rebate — which are the
  common cases, and would leave payables wrong in the meantime.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py               # four operations, two control rows
packages/reality-core/src/reality/services/exceptions.py         # two derivations, registry, order
packages/reality-core/src/reality/catalogs.py                    # class order
packages/reality-core/config/operational_exception_catalog.yaml  # the classes and their guidance
packages/reality-core/config/command_catalog.yaml                # commands, parameters, coverage, guidance
packages/reality-core/config/tenant_isolation_catalog.yaml       # operations and tools
packages/reality-core/src/reality/tools/application.py           # agent tools
packages/reality-core/src/reality/mcp/catalog.py                 # tool schemas
packages/reality-core/src/reality/web/api.py                     # endpoints
docs/features/ledger.md, operational_exceptions.md, procure_to_pay.md
apps/docs/content/catalogs/ (+ de/)                               # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                      # specification row
```

## Design

### The mirror, exactly

| Selling side | Buying side |
|---|---|
| `credit_note` posts debit `sales_revenue`, credit `accounts_receivable` | `supplier_credit_note` posts debit `accounts_payable`, credit `inventory` |
| `customer_refund` posts debit `accounts_receivable`, credit `cash` | `supplier_refund` posts credit `accounts_payable`, debit `cash` |
| control `("accounts_receivable", "credit")` | control `("accounts_payable", "debit")` |
| control `("accounts_receivable", "debit")` | control `("accounts_payable", "credit")` |

Two rows in `SETTLEMENT_CONTROL` and `open_invoice_amount` answers for both without being
touched: it already takes the balance on the control account for that document and flips its
sign by the control entry's own side. A supplier credit note sitting on the debit side of
accounts payable is a claim on the supplier, and that is what the function returns.

Netting a supplier credit against a supplier invoice is two control entries on opposite sides of
`accounts_payable`, which is precisely what `allocate_settlement` already requires. Nothing
downstream — the aging register, `overdue_payable`, `purchase_discount_available` — needs telling
that a credit was involved, because a payable falls the same way whatever settled it.

### Why the reverse of the invoice and not something cleverer

`post_supplier_invoice` debits `inventory` and credits `accounts_payable`. The credit note is the
exact opposite of that with the same amount. It would be possible to argue about which account
should absorb a rebate rather than a returned item, and that argument is accounting, which this
product is not doing. The reverse of the original posting is the one answer that needs no
judgement and no figure nobody stated.

### Posting without an invoice

Deliberately allowed, exactly as on the selling side. The claim exists whether or not anything is
open, and a payable going the other way is the statement that the supplier owes this company —
which is what a credit against an already-paid invoice is. That case is why the refund exists.

### The two classes

`supplier_credit_unposted` mirrors `credit_note_unposted` and uses the same learned *rule*: the
median of the most recent completed cases times three, with a floor, and silence below a minimum
history.

It does **not** share the selling side's threshold, and the first draft of this plan said it
should. That was wrong on inspection. The existing threshold is learned from credit notes the
company wrote itself and booked to `sales_revenue` — how long accounts receivable takes over its
own paperwork. Booking a credit a supplier sent is a different process with a different owner,
and sharing the number would let one side's rhythm accuse or silence the other. A company that
issues no sales credits at all would never judge its supplier credits.

So the rule is generalised and each class learns from its own population, which is exactly what
spec 080 did when it gave the learned-expectation rule two more users: `order_stalled` and
`receipt_unbilled` share the rule and share no statistic. `_credit_notes`, `_credit_is_posted`
and `_credit_posting_threshold` each take the document type and control account they are asking
about, and neither side can silently start reading the other's documents.

`supplier_credit_unclaimed` mirrors `credit_note_unsettled` and has no threshold, because the
claim exists from the moment the credit is booked.

Both read only documents of type `supplier_credit_note`, and the two existing classes keep
reading only `credit_note`. That separation is a test rather than a comment.

### What "posted" means on this side

The selling-side check reads the `sales_revenue` balance for the document. The mirror reads
`inventory`, which is the account the supplier invoice moved and the credit note moves back.

### Data and migration impact

None. No column, no revision, no backfill.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | service | `test_credit_notes.py::test_a_supplier_credit_note_posts_the_reverse` | the type is not settleable |
| FR-002 | service | `test_credit_notes.py::test_a_supplier_credit_note_posts_once_and_for_something` | a second posting is accepted |
| FR-003 | service | `test_a_supplier_credit_note_posts_the_reverse` | no control entry is found |
| FR-004 | service | `test_credit_notes.py::test_a_supplier_credit_settles_only_its_own_supplier` | another party's invoice is netted |
| FR-005 | service | `test_credit_notes.py::test_netting_leaves_the_remainder_open` | the excess disappears |
| FR-006 | service | `test_credit_notes.py::test_a_supplier_refund_settles_the_credit` | money cannot come back |
| FR-007 | service | `test_a_supplier_refund_settles_the_credit` | more than the claim is refunded |
| FR-008 | story | `test_credit_notes.py::test_a_credit_takes_a_payable_off_the_overdue_queue` | the payable stays overdue |
| FR-009 | story | `test_derivation.py::test_supplier_credit_unposted` | class is not derived |
| FR-009 | story | `test_derivation.py::test_each_side_learns_its_own_rhythm` | one side's history judges the other |
| FR-010 | story | `test_derivation.py::test_supplier_credit_unclaimed` | class is not derived |
| FR-011 | story | `test_derivation.py::test_the_two_credit_sides_stay_apart` | one side reports the other's documents |
| FR-012 | service | `test_derivation.py::test_the_supplier_credit_entries_expose_full_shape` | causal values missing |
| FR-013 | story | `test_derivation.py::test_the_supplier_credit_entries_clear_through_reality` | an entry survives its fix |
| FR-014 | service | `test_explanation.py::test_supplier_credit_explanation_and_not_found_parity` | identity unknown to explanation |
| FR-015 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-016 | unit | `test_application_catalog.py`, `tests/tenant_isolation/`, `test_capability_guidance.py` | catalog drift |
| FR-017 | story | `test_derivation.py::test_the_supplier_credit_entries_order_deterministically` | order varies between reads |
| FR-018 | story | every existing suite, unchanged | an existing behaviour moves |
| DR-001 | review | no file under `migrations/versions/` is added | — |
| DR-002 | story | `test_the_supplier_credit_entries_clear_through_reality` | something persists |
| DR-003 | service | `test_credit_notes.py::test_one_allocation_service_settles_both_sides` | a second settlement path appears |
| DR-004 | service | `test_the_supplier_credit_entries_expose_full_shape` | trace restates business fields |
| DR-005 | story | `test_derivation.py::test_the_supplier_credit_classes_are_tenant_scoped` | another tenant is read |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |
| DR-007 | service | `test_a_supplier_credit_note_posts_the_reverse` | a posted figure was derived |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and nothing stored changes. Rollback is a plain revert.

The visible effect is confined to tenants that record supplier credit notes, which is none
today, because the type could not be posted. Nothing existing changes behaviour.

The demo month records no supplier credit and will not change.

## Review Risks

- **The recorded gap said "no `supplier_credit_note` type exists", and that overstated it.**
  `create_document` takes the type as a free string, so such a document could always be created;
  what could not happen was posting it, settling it or seeing it. The distinction matters for
  anyone reading the note later, and it is the second time in this series that a recorded
  blocker turned out to be narrower than it sounded.
- **This is a mirror and mirrors invite drift.** The two sides now have four near-identical
  operations and four near-identical classes, and the danger is not today's diff but the next
  change made to one side only. The mitigation is that both sides share one settlement service
  and one parameterised learned rule, and that the separation between them — which documents each
  reads and which account each judges — is asserted by a test rather than left to reading.
- **The money half without the goods half is a genuine half-feature.** A credit for goods that
  went back is recorded with no movement behind it, because a supplier return cannot be recorded
  at all. For a price correction or a rebate that is complete and correct; for a physical return
  it is money without evidence of the goods. It is named in the specification and in the
  remaining-gap note rather than hidden.
- **Crediting `inventory` is a choice a bookkeeper might argue with.** A rebate arguably belongs
  somewhere else. The answer is that the exact reverse of the original posting needs no
  judgement and invents no figure, and that adjudicating rebate treatment is accounting this
  product does not do.
- **Two more classes on an already long queue.** Both are silent for a company whose suppliers
  send no credits, and neither can fire on a document type that could not previously exist.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
