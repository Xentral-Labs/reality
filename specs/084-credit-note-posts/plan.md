# Implementation Plan: A Credit Note Gives the Money Back

**Branch**: `084-credit-note-posts` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

A credit note becomes what an invoice already is: a document that posts and is settled. The
settlement machinery learns that a document worth settling is not always an invoice, which is
the one real change here — everything else follows from it.

No schema. The catalog gains two classes, and one existing class stops implying something it
never measured.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; no schema change
**Testing**: pytest business stories under `tests/` and `tests/operational_exceptions/`
**Project Type**: backend service consumed by Web, MCP, and Chat adapters
**Constraints**: Decimal money; balanced postings; opaque IDs; strict tenant scope
**Scale/Scope**: Two posting operations, one widened settlement concept, two derivations

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The credit note is Evidence somebody recorded; posting makes it Reality in the ledger, and the trace reaches the document, its control entry and its SourceRecord by opaque identity | PASS |
| Reality owns operational state | Nothing gains a status. Whether a credit note is posted, allocated or refunded is derived from whether those records exist | PASS |
| Proven schema only | No schema change. Document, LedgerEntry, posting groups and the settlement relation all exist; this feature uses them for documents that were left out | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; what an invoice still owes keeps coming from the existing shared settlement derivation rather than a second one | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | A credit is a document a person can inspect, with a posting group and an allocation, rather than an amount that appeared against an invoice | PASS |
| Received values not recomputed | The posted amount is the total the credit note states. Adding its lines up to post a different figure would make Reality the author of somebody else's number | PASS |
| Smallest coherent design | Four alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Keep `post_sales_credit` and expose it.** One endpoint and one tool entry, and it leaves
  the product unable to credit a paid invoice — the ordinary consumer return — while keeping
  two ways to reduce a receivable and a credit note that means nothing.
- **Let a credit reduce an open receivable only.** What the previous draft of this
  specification proposed, abandoned on the same finding: `allocate_settlement` refuses more
  than an invoice's open amount, so a customer who has paid cannot be credited at all.
- **Post the credit note automatically when it is recorded.** Removes one new class by removing
  the condition, and removes a real business fact with it: the paperwork exists and the money
  has not moved.
- **Make `returned_not_credited` require a posted credit.** One class instead of three, and one
  class doing two jobs: it would stop answering the quantity question it was built for.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py               # two postings, the widened control entry, the old operation removed
packages/reality-core/src/reality/web/api.py                     # two endpoints
packages/reality-core/src/reality/mcp/catalog.py                 # two agent tools
packages/reality-core/config/command_catalog.yaml                # the commands and their parameters
packages/reality-core/config/tenant_isolation_catalog.yaml       # the new public operations
packages/reality-core/src/reality/services/exceptions.py         # the norm, two derivations, registry, order
packages/reality-core/src/reality/catalogs.py                    # class order
packages/reality-core/config/operational_exception_catalog.yaml  # two classes, and the guidance fix on an existing one
packages/reality-core/src/reality/demo/normal_month.py           # the demo credits and settles the new way
packages/reality-core/tests/                                     # posting, settlement, derivation and explanation proof
docs/features/ledger.md                                          # a credit note posts and is settled
docs/features/operational_exceptions.md                          # taxonomy rows
apps/docs/content/catalogs/*.md (+ de/)                           # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                     # specification row
```

## Design

### The change that makes the rest possible

`_invoice_control_entry` refuses any document that is not a `sales_invoice` or a
`supplier_invoice` — "Settlement target is not an invoice." Everything downstream inherits
that: `open_invoice_amount` calls it, `allocate_settlement` calls that, and so a credit note
can be neither settled nor measured.

It becomes `_settlement_control_entry` and knows four documents rather than two:

| Document | Control account | Side |
|---|---|---|
| `sales_invoice` | accounts_receivable | debit |
| `supplier_invoice` | accounts_payable | credit |
| `credit_note` | accounts_receivable | credit |
| `customer_refund` | accounts_receivable | debit |

`open_invoice_amount` already turns a side and a balance into "what is still outstanding on
this document", so it generalises without changing: a credit note's outstanding amount is what
the company still owes on it. Its name stays, because renaming a public function used by the
aging register, the isolation catalog and four classes is a change with no benefit to this
feature; its docstring says that "invoice" here means any document settlement can settle.

### Posting a credit note

`post_sales_credit_note(session, tenant_id, credit_note_id)` records the exact reverse of
`post_sales_invoice` — revenue debited, receivable credited — for the total the credit note
states. It takes **no invoice**, because the obligation exists whether or not one is open. The
receivable going negative is the statement that the company owes the customer.

Refused for a document that is not a credit note, one already posted, and a total of zero or
less.

### Settling it

Two ways, both through the relation payments already use:

- **Netted.** `allocate_settlement(credit_control, invoice_control, amount)` against an open
  invoice of the same customer. The invoice's open amount falls exactly as a payment makes it
  fall, so the aging register and the receivable class need telling nothing.
- **Refunded.** `post_customer_refund(session, tenant_id, credit_note_id, amount)` records a
  `customer_refund` document — cash credited, receivable debited — and allocates it against the
  credit note, mirroring `post_customer_payment` line for line.

The existing over-allocation guards then do the work unchanged: nothing may settle more than
the credit note still owes, currencies must match, and reversed posting groups are excluded.

The old `post_sales_credit(invoice_id, amount)` goes. Leaving it would be a second way to
reduce a receivable, and the demo — its only caller — moves to the new operations.

### The two classes

`credit_note_unposted` walks credit notes with no posting and reports those older than a
learned threshold, another use of Spec 080's helper with its own floor.

`credit_note_unsettled` walks posted credit notes and reports what is neither allocated nor
refunded. It needs no threshold at all: the amount is owed from the moment it is posted, and
the entry shrinks as each part is settled.

The existing `unmatched_financial_event` does not cover this and should not be widened to. It
walks control entries whose posting group contains cash, which is what makes it "money moved
and nobody said what for". A credit note moves no cash, so it is a different condition with a
different owner.

### The guidance fix

`returned_not_credited` measures whether the goods that came back have been credited on paper.
An operator reading "credited" will assume money moved. Its description gains a sentence
saying what it covers and naming the two classes that cover the rest. This is a deliberate
change to an existing class and carries its own requirement and test, because it is the kind of
change a diff swallows.

### Data and migration impact

None. No column, no revision, no backfill. Credit notes already recorded stay unposted, which
is what they are.

### Failure, security, and tenant behavior

Every refusal happens at the point of posting or settling with a message naming what is wrong.
Every derivation filters `tenant_id`, including the norm.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `tests/test_credit_notes.py::test_a_credit_note_posts_the_reverse_of_an_invoice` | the operation does not exist |
| FR-001 | unit | `tests/test_credit_notes.py::test_a_paid_invoice_can_still_be_credited` | the credit is refused |
| FR-002 | unit | `tests/test_credit_notes.py::test_the_stated_total_is_what_posts` | the lines are summed |
| FR-003 | unit | `tests/test_credit_notes.py::test_posting_is_refused_where_it_would_be_wrong` | every refusal is accepted |
| FR-004 | unit | `tests/test_credit_notes.py::test_a_credit_may_be_netted_against_an_open_invoice` | settlement refuses a credit note |
| FR-005 | unit | `tests/test_credit_notes.py::test_a_credit_may_be_refunded` | the refund operation does not exist |
| FR-006 | unit | `tests/test_credit_notes.py::test_settling_is_refused_beyond_what_is_owed` | over-settlement accepted |
| FR-007 | adapter | endpoint test in `tests/test_master_data_api.py`; tool assertion in `tests/test_application_catalog.py` | neither surface offers them |
| FR-008 | story | `test_derivation.py::test_credit_note_unposted` | class is not derived |
| FR-009 | story | `test_derivation.py::test_credit_note_unsettled` | class is not derived |
| FR-010 | story | `test_derivation.py::test_the_posting_norm_describes_this_tenant` | no norm is derived |
| FR-011 | service | `test_derivation.py::test_credit_note_classes_expose_full_entry_shape` | causal values missing |
| FR-012 | service | `test_credit_note_classes_expose_full_entry_shape` | trace keys missing |
| FR-013 | story | `test_derivation.py::test_credit_note_classes_clear_through_reality` | entries persist after posting and settling |
| FR-014 | service | `test_explanation.py::test_credit_note_classes_explanation_and_not_found_parity` | identities unknown to explanation |
| FR-015 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-016 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| FR-017 | story | `test_derivation.py::test_credit_note_classes_order_longest_first` | order varies between reads |
| FR-018 | unit | `test_coverage.py` guidance assertion naming both money classes | the sentence is absent |
| DR-001 | review | no file under `migrations/versions/` is added | — |
| DR-002 | story | `test_credit_note_classes_clear_through_reality` | something persists |
| DR-003 | unit | `test_the_stated_total_is_what_posts` | a sum appears |
| DR-004 | unit | `test_a_credit_may_be_netted_against_an_open_invoice` | a second settlement path appears |
| DR-005 | story | `test_credit_note_classes_clear_through_reality` | a status is written |
| DR-006 | service | `test_credit_note_classes_expose_full_entry_shape` | trace restates business fields |
| DR-007 | story | `test_derivation.py::test_credit_note_classes_are_tenant_scoped` | cross-tenant rows leak |
| DR-008 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |
| DR-009 | review | `post_sales_credit` no longer exists and nothing calls it | — |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no stored value changes. Rollback is a plain revert.

The demo month changes deliberately: it credits 100 against an invoice today through an
operation nobody can reach, and will record, post and settle a credit note instead.
`test_the_month_ends_with_exactly_these_exceptions` will notice any change to the queue, and
whatever it shows must be argued rather than absorbed.

## Review Risks

- **Widening a settlement concept is the real change here.** Everything else follows from
  `_settlement_control_entry` knowing four documents rather than two. A reviewer should check
  that the two new rows are right, because a wrong side or a wrong account would put money on
  the wrong side of the books silently — the postings would still balance.
- **`open_invoice_amount` now answers a question wider than its name.** Renaming it would ripple
  through the aging register, the isolation catalog, four classes and the docs for no benefit
  here, so the name stays and the docstring carries the truth. That is a compromise, and a
  reviewer may prefer the rename.
- **Credit notes are low-volume, and the unposted class needs history.** A business issuing a
  handful a year may never reach the minimum and never be judged. The unsettled class does not
  share this weakness, which is part of why there are two.
- **Removing a public operation.** `post_sales_credit` is a shared service function. Nothing
  outside the repository calls it and the demo is its only caller, but that is confirmed in the
  final review rather than assumed here.
- **One class's guidance is edited by another class's feature.** Deliberate and the honest half
  of this work, and exactly the kind of change that gets lost in a diff, so it carries its own
  requirement and its own test.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
