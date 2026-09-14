# Implementation Plan: Two Answers the Records Already Hold

**Branch**: `078-records-already-answer` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Two derivations over records that exist, no schema and no new rule about time. The first
reads a Party field nothing has ever read and compares it with the outstanding amount the
open-item derivation already produces. The second groups supplier invoices by the number
their supplier put on them.

The catalog goes from thirteen classes to fifteen, and `party` becomes the ninth
authoritative record type.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; no schema change
**Testing**: pytest business stories under `tests/operational_exceptions/`
**Project Type**: backend service consumed unchanged by Web, MCP, and Chat adapters
**Constraints**: Decimal money; opaque IDs; strict tenant scope
**Scale/Scope**: Two derivations, one new record type, no migration

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Both read Evidence the tenant already owns. The credit class traces to the Party and to the invoices behind the figure; the duplicate class traces to both documents and their SourceRecords, which is what tells an operator whether the second arrived from a connector or was typed | PASS |
| Reality owns operational state | Neither writes anything and neither adds a status. A Party gains no flag and a Document gains no marker; both entries are derived per read | PASS |
| Proven schema only | No schema change at all. Both conditions are answerable from records that exist, which is the whole point of doing these two first | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; the outstanding figure comes from the existing shared open-item derivation rather than a second query | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Each entry returns the two figures or the two documents it compares, so a judgement can be checked rather than believed | PASS |
| Received values not recomputed | The credit limit is a value a person recorded and is read as it stands. The outstanding amount is taken from the shared settlement derivation and never rebuilt from postings — a second sum would be a second authority for one number. Comparing the two received values is what principle VIII encourages | PASS |
| Smallest coherent design | Three alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Refuse a duplicate supplier invoice at write time.** Smaller, and wrong for this model:
  Reality records what a source states and judges afterwards, and the same invoice
  legitimately arrives from two connectors. Refusing would destroy the evidence that both
  arrived and would move a judgement into the write path, where it cannot be explained.
- **Sum the outstanding amount from ledger entries directly.** Fewer moving parts and a
  second authority for a number the product already derives once. Rejected on principle VIII
  and on the practical ground that it would drift from the aging register.
- **Count unshipped orders towards the limit.** Closer to what a credit controller means by
  exposure, and a different feature: it changes what the number is, needs a decision about
  which promises count, and would make this spec about defining exposure rather than about
  reading a field.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/exceptions.py         # two derivations, registry, order
packages/reality-core/src/reality/catalogs.py                    # class order
packages/reality-core/config/operational_exception_catalog.yaml  # two classes and guidance
packages/reality-core/tests/operational_exceptions/              # derivation and explanation proof
docs/features/operational_exceptions.md                          # taxonomy rows
apps/docs/content/catalogs/exceptions.md (+ de/)                  # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                     # specification row
```

**Files/layers affected**: the exception service and the catalog. No model, no migration, no
transport, no frontend.

## Design

### Credit exposure

`_credit_limit_exceeded_exceptions` reads Parties whose `credit_limit` is above zero, sums
the open balances the shared open-item derivation reports for their sales invoices, and
reports the excess.

Three rules keep it honest. A limit of zero means none is recorded, because the column
defaults to zero and reading that as "carries nothing" would report every customer on the
day the class ships. Only open items in the Party's own `default_currency` are counted, for
the reason Spec 076 gave about units: a converted figure is a guess. And an amount equal to
the limit is not an excess, because the agreed number is allowed.

The entry is carried by the Party, which makes `party` the ninth record type. That is the
right carrier: the condition is about a relationship, not about any one invoice, and the
operator's next act is a decision about the customer.

Sorting is on the oldest open item behind the excess, so the longest-standing exposure
comes first.

### Duplicate supplier invoices

`_duplicate_supplier_invoice_exceptions` groups supplier invoices by Party and by their
number with surrounding whitespace removed and case ignored, and reports every document
after the first in each group.

"First" has to be deterministic or the pair would swap between reads. Documents are ordered
by `document_date` and then by `id`, which is the ordering `financial_open_items` already
uses; `id` breaks the tie when two arrive on the same day, and it is stable because it never
changes.

The grouping reads Documents directly rather than the open-item derivation, because an
invoice that has not been posted yet does not appear in open items at all — and a duplicate
caught before posting is the one worth catching. A document whose posting has been reversed
is skipped on both sides of the comparison, since a withdrawn invoice cannot be paid twice
and a supplier reissuing a corrected invoice under its original number is ordinary.

A document with an empty number is neither reported nor matched against. An empty string is
not a number two documents can share, and grouping on it would report every unnumbered
document as a duplicate of every other.

The entry is carried by the later document and names the earlier one in both its causal
values and its trace, including both SourceRecords: that is what tells an operator whether
the second was typed in or arrived from a connector, which decides what they do about it.

Sorting is on the later document's date.

### Identity and guidance

Identities are `exc__credit_limit_exceeded__{party_id}` and
`exc__duplicate_supplier_invoice__{document_id}`. The credit class sorts beside the
receivable it is about; the duplicate class sorts beside the payable.

Spec 071's cross-reference rule applies. `credit_limit_exceeded` and `overdue_receivable`
are confusable — both are about a customer owing money — and must name each other: one is
about the total agreed, the other about a single invoice being late, and a customer can be
in either without the other. `duplicate_supplier_invoice` sits beside `overdue_payable` and
`billed_not_received` as the third thing that can be wrong about a supplier invoice.

### Data and migration impact

None. No column, no revision, no backfill.

### Failure, security, and tenant behavior

Every query filters `tenant_id`. Explanation re-derives, so cleared identities produce the
existing `NotFound`. Neither class exposes a figure a Party is not entitled to see, because
both are already visible in the registers.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | story | `test_derivation.py::test_credit_limit_exceeded` | class is not derived |
| FR-002 | story | `test_derivation.py::test_a_party_without_a_limit_is_never_reported` | zero is read as a limit |
| FR-003 | unit | `test_derivation.py::test_credit_exposure_uses_the_shared_open_items` | a second sum appears |
| FR-004 | story | `test_derivation.py::test_only_the_partys_own_currency_counts` | currencies are added together |
| FR-005 | story | `test_credit_limit_exceeded` | the boundary is reported |
| FR-006 | story | `test_derivation.py::test_duplicate_supplier_invoice` | class is not derived |
| FR-007 | story | `test_derivation.py::test_numbers_are_matched_without_case_or_padding` | padded numbers miss |
| FR-008 | story | `test_derivation.py::test_the_original_is_the_same_document_every_read` | the pair swaps |
| FR-008a | story | `test_derivation.py::test_a_reversed_invoice_is_not_a_duplicate` | a corrected reissue is reported |
| FR-009 | service | `test_derivation.py::test_both_classes_expose_full_entry_shape` | causal values missing |
| FR-010 | service | `test_both_classes_expose_full_entry_shape` | trace keys missing |
| FR-011 | story | `test_derivation.py::test_both_classes_clear_through_reality` | entries persist after settlement |
| FR-012 | service | `test_explanation.py::test_record_classes_explanation_and_not_found_parity` | identities unknown to explanation |
| FR-013 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-014 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| FR-015 | story | `test_the_original_is_the_same_document_every_read` | order varies between reads |
| DR-001 | story | `test_both_classes_clear_through_reality` | something persists |
| DR-002 | unit | `test_credit_exposure_uses_the_shared_open_items` | a second authority appears |
| DR-003 | service | `test_both_classes_expose_full_entry_shape` | record type wrong |
| DR-004 | service | `test_both_classes_expose_full_entry_shape` | trace restates business fields |
| DR-005 | story | `test_derivation.py::test_record_classes_are_tenant_scoped` | cross-tenant rows leak |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |
| DR-007 | review | no file under `migrations/versions/` is added | — |

Every negative test carries a positive control in the same test: the same setup with the one
distinguishing fact changed, asserting the entry does appear. A negative written before the
class exists otherwise passes for the wrong reason, which has happened in three specifications
already.

## Rollout and Rollback

No migration and no stored value changes. Rollback is a plain revert. The visible effect is
two new kinds of row in a queue that already carries thirteen.

The first-read volume is worth measuring for the credit class. On a tenant that has recorded
limits and never looked at them, every customer past their limit appears at once — which is
correct and may still be a large number. The measurement should say how large on the demo
tenant rather than assert that it is small.

## Review Risks

- **Zero as "no limit" is a convention, not a fact.** A company that genuinely wants a
  customer on cash-only terms would record zero and expect every open invoice reported. They
  will get silence. The alternative reports every customer of every tenant on day one, so
  the convention is the lesser wrong — but it is a wrong, and the guidance text has to say
  so plainly rather than leave an operator guessing.
- **A supplier that reuses numbers across years.** Two genuine invoices numbered `4711` in
  2025 and 2026 produce a false entry. The operator resolves it by looking at two documents,
  which is cheap; the opposite error is a second payment.
- **`party` as a carrier is new.** Eight record types have been documents, lines,
  commitments, movements, items, ledger entries, import jobs and source capabilities — all
  transactions or things. A Party is a relationship, and every consumer reading `record_type`
  should be checked, as it was for `document_line` in Spec 076.
- **Two unrelated conditions in one specification.** They share a shape — an answer the
  records already hold — and nothing else. A reviewer who thinks that is too thin a thread
  should say so; the alternative is two specifications with one derivation each.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
