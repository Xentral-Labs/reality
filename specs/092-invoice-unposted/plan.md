# Implementation Plan: The Invoice Nobody Booked

**Branch**: `092-invoice-unposted` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Two classes from a body that already exists and already takes exactly the two parameters they
need. The catalog goes from twenty-nine to thirty-one, no schema, no service change, and the
helpers lose the word "credit" from their names because they were never about credits.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; no schema change
**Testing**: pytest business stories under `tests/operational_exceptions/`
**Project Type**: backend service consumed unchanged by Web, MCP, CLI and Chat adapters
**Constraints**: Learned norms only; nothing stored; opaque IDs; strict tenant scope
**Scale/Scope**: Two derivators, two constants, one rename

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The document is Evidence the tenant recorded and the ledger is Reality; the class reports the distance between them | PASS |
| Reality owns operational state | Nothing gains a status; both entries are derived per read and stored nowhere | PASS |
| Proven schema only | No schema change and no service change | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; all four unposted classes share one body and one rule | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Each entry names the amount, how long it has stood, and the norm it was judged against | PASS |
| Received values not recomputed | The amount reported is the document's own gross amount; the threshold is an observation over this tenant's own history, stored nowhere | PASS |
| Smallest coherent design | Three alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **One `invoice_unposted` class for both directions.** Fewer classes and a worse worklist: a
  sales invoice nobody booked hides money owed *to* the company and belongs to billing; a
  supplier invoice hides money the company owes and belongs to accounts payable. Spec 089 made
  this argument for the credit notes and it holds identically here.
- **Reuse the credit note's learned threshold.** The mistake Spec 089's first draft made, and the
  reason its plan now says share the rule and never the history. Four document types, four
  processes, four rhythms.
- **Report anything recorded and unbooked, with no norm.** It would report every invoice recorded
  today and be scrolled past by tomorrow. The learned norm is what makes the class survivable.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/exceptions.py         # two constants, two derivators, one rename
packages/reality-core/src/reality/catalogs.py                    # class order
packages/reality-core/config/operational_exception_catalog.yaml  # the classes and their guidance
packages/reality-core/tests/operational_exceptions/              # derivation and explanation proof
docs/features/operational_exceptions.md, ledger.md
apps/docs/content/catalogs/ (+ de/)                               # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                      # specification row
```

## Design

### The body already fits

Spec 089 generalised the unposted body to take the document type it reads and the account that
says the document was booked, so the buying side could reuse it. Adding invoices needs two
constants and two four-line derivators:

```
SALES_INVOICE    = ("sales_invoice",         "sales_revenue")
SUPPLIER_INVOICE = ("supplier_invoice",      "accounts_payable")
SALES_CREDIT     = ("credit_note",           "sales_revenue")
SUPPLIER_CREDIT  = ("supplier_credit_note",  "accounts_payable")
```

Both accounts are the ones the posting services themselves use to refuse a second posting, so
"booked" means the same thing to the class as it does to the operation.

**Checking that turned up an inconsistency in Spec 089.** `supplier_credit_unposted` asks
`inventory` while `post_supplier_credit_note` refuses a second posting on `accounts_payable`. The
two are equivalent in practice — one posting touches both accounts, so either is non-zero exactly
when the document is booked — so nothing was wrong and nothing will change. But a class and its
operation disagreeing about what "booked" means is the kind of small divergence that is true
until somebody changes one posting, and it is cheap to remove while the four constants are being
written down together. It is corrected here, with the existing suite as the evidence that no
behaviour moved.

The helpers are renamed — `_credit_notes` to `_documents_of_type`, `_credit_is_posted` to
`_is_posted`, `_credit_posting_threshold` to `_posting_threshold`, `_unposted_credit_exceptions`
to `_unposted_document_exceptions`. They were named after the only caller they had, and keeping
the name once they serve four document types would be the sort of small lie that makes the next
reader distrust the rest.

### Four rhythms, one rule

Each class learns from its own document type. The rule — the median of this tenant's most recent
completed cases times three, with a fortnight floor and silence below five cases — is shared, and
no history is. That is Spec 080's precedent and Spec 089's correction, and it matters more here
than anywhere: a company that books its sales invoices daily and its supplier invoices at month
end has two honest rhythms, and one judging the other would accuse it of both.

### Why this class will actually speak

The credit-note classes have a known weak point: credit notes are rare, so a company issuing a
handful a year never reaches the minimum history and is never judged. Invoices are the opposite.
Any trading company books enough of them for a rhythm to exist, which makes these two the first
learned classes in the catalog that will be live on almost every tenant.

That cuts both ways and is the main review risk below.

### The reversal case answers itself

A reversal posts inverse entries with **no document reference** — `document_id=None`. So the
original document's balance on its control account is unchanged, it still reads as booked, and it
is not reported. That is also the right answer: somebody booked it and then deliberately unbooked
it, which is not the same as nobody having got round to it. It is non-obvious enough to be worth
a test rather than a comment.

### Data and migration impact

None.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | story | `test_derivation.py::test_sales_invoice_unposted` | class is not derived |
| FR-002 | story | `test_derivation.py::test_supplier_invoice_unposted` | class is not derived |
| FR-003 | story | `test_derivation.py::test_each_document_type_learns_its_own_rhythm` | one rhythm judges another |
| FR-004 | story | `test_sales_invoice_unposted` | a tenant with no history is judged |
| FR-005 | story | `test_derivation.py::test_a_reversed_posting_is_not_an_unbooked_one` | a reversal is reported |
| FR-006 | story | `test_derivation.py::test_a_document_with_no_date_says_nothing` | an undated document is reported |
| FR-007 | story | `test_derivation.py::test_the_four_unposted_sides_stay_apart` | one class reads another's documents |
| FR-008 | service | `test_derivation.py::test_the_unposted_invoice_entries_expose_full_shape` | causal values missing |
| FR-009 | story | `test_sales_invoice_unposted` | booking does not clear it |
| FR-010 | service | `test_explanation.py::test_unposted_invoice_explanation_and_not_found_parity` | identity unknown to explanation |
| FR-011 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-012 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| FR-013 | story | `test_derivation.py::test_the_unposted_invoice_entries_order_deterministically` | order varies between reads |
| FR-014 | story | every existing suite, unchanged | an existing behaviour moves |
| FR-015 | unit | `test_derivation.py::test_a_class_and_its_operation_agree_on_booked` | a class asks a different account from its operation |
| DR-001 | review | no diff under `services/core.py` and none under `migrations/versions/` | — |
| DR-002 | story | `test_sales_invoice_unposted` | something persists |
| DR-003 | unit | `test_derivation.py::test_all_four_unposted_classes_share_one_body` | a second body appears |
| DR-004 | service | `test_the_unposted_invoice_entries_expose_full_shape` | trace restates business fields |
| DR-005 | story | `test_derivation.py::test_the_unposted_invoice_classes_are_tenant_scoped` | another tenant is read |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and nothing stored changes. Rollback is a plain revert.

The demo month books everything it records, so its queue is unchanged and the pinned test proves
it.

## Review Risks

- **These are the first learned classes that will be live on almost every tenant.** The
  credit-note ones are usually silent for want of history; these will not be. If the learned
  constants are wrong — and they have never been checked against a real business — this is where
  it will show first. That is an argument for shipping it, not against, but the first real tenant
  should be watched.
- **A company that books nothing is told nothing.** The minimum history protects against
  flooding an imported tenant and, in the same move, stays quiet for the company that most needs
  telling. That is the honest shape of a learned rule and it is the same weak point the
  credit-note classes carry.
- **Four unposted classes is a lot of catalog for one idea.** Each has a different owner and a
  different direction of money, and all four share one body — but a reviewer who thinks the
  taxonomy is getting wide is raising a fair point about the split, not about the code.
- **A shipped class's definition of "booked" changes account, with no behaviour change.**
  `supplier_credit_unposted` moves from `inventory` to `accounts_payable` to match its own
  operation. The two are equivalent for every document the product can produce, and the existing
  suite is the evidence — but it is a change to a shipped class and should be read as one.
- **Renaming four helpers touches code four shipped classes depend on.** The existing suites
  passing untouched is the evidence that nothing moved, and the rename is mechanical.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
