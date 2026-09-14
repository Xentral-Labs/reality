# Implementation Plan: Overdue Payables

**Branch**: `074-trade-control-gaps` | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One class, and it is the receivable's mirror. The payable adds no rule of its own: the open
item exception becomes a single function parameterised by document type, and the payable is
one of its two callers.

The feature is small because three of the four conditions originally proposed for it turned
out to be either unreachable or unexpressible. That reduction is recorded in the
specification rather than hidden, and it is the more useful half of this work.

No schema, no migration, no persisted state, no adapter and no frontend change.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; no new table, column, or index
**Testing**: pytest business stories under `tests/operational_exceptions/`
**Project Type**: backend service consumed unchanged by Web, MCP, and Chat adapters
**Constraints**: Decimal amounts; UTC instants; opaque IDs; strict tenant scope
**Scale/Scope**: One class, no new cause, one extraction

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Derived from the tenant's own supplier invoice, its payment term and its control ledger entry; the trace reaches invoice, control entry and SourceRecord by opaque identity | PASS |
| Reality owns operational state | Derived per read, cleared by payment or reversal; no status written to an invoice | PASS |
| Proven schema only | No schema change. The three conditions that would need one are excluded and named, so a later specification can use them as its proof | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; the class consumes existing shared derivations and adds no public surface | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | Explanation re-derives and returns the due date, days overdue and outstanding amount, so the judgement can be checked | PASS |
| Smallest coherent design | Four alternatives rejected below, three of them by what the model does not permit | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Copy the receivable derivation and change the document type.** Rejected: it would put
  two functions in charge of what an overdue open item is, which is the duplication Spec 069
  spent its whole scope removing.
- **Add a class for goods moved beyond a commitment.** Specified, implemented, and then
  removed: `record_movement` refuses a movement beyond the commitment's open quantity, no
  operation reduces a commitment's quantity afterwards, and a correction carries no
  commitment reference. The condition cannot arise.
- **Add a class for negative stock.** Rejected for the same kind of reason: outbound
  movements are refused beyond the stock at their location, and a correction is refused when
  later movements depend on the stock it would remove.
- **Match invoices to orders by party and period to deliver the three-way check.** Rejected:
  the model has no document-to-document reference and invoices never come from a source
  record, so any match would guess.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/exceptions.py  # one parameterised open-item rule
packages/reality-core/src/reality/catalogs.py             # class order
packages/reality-core/config/operational_exception_catalog.yaml  # the class and its guidance
packages/reality-core/tests/operational_exceptions/       # derivation, coverage, explanation proof
docs/features/operational_exceptions.md                   # durable business contract
apps/docs/content/catalogs/exceptions.md (+ de/)          # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                              # spec and evidence rows
```

**Files/layers affected**: one service module and the catalog. No new public service
function, so the tenant isolation catalog stays untouched.

## Design

### One open-item rule, two sides

`_receivable_exceptions` walked the aging register, kept unsettled sales invoices and
reported those past their derived due date. The document type, the class id and the title
are the only things that differ on the payable side, so the body becomes
`_open_item_exceptions` with those three as parameters and two thin derivators over it. The
due date, the outstanding amount, the settled and reversed exclusions and the term cascade
all stay where they are, which is what keeps the two sides agreeing by construction rather
than by review.

### Identity, ordering and guidance

The identity is `exc__overdue_payable__{document_id}`; the carrier is the invoice Document,
already a known record type. The entry sorts on its due date, longest overdue first, exactly
as the receivable does. The declared order gains one entry beside the receivable, ahead of
the unmatched financial event.

Spec 071's cross-reference rule applies to two new pairs. The payable and the receivable are
mirror images. The payable and `overdue_incoming_supplier_commitment` are the easier
confusion in practice: both concern a supplier being late, one with goods and one with
money. Both existing descriptions are amended so each pair names its sibling from both
sides.

### Data and migration impact

None.

### Failure, security, and tenant behavior

Every query filters `tenant_id`. Explanation re-derives, so a settled, malformed, unknown or
foreign identity produces the existing `NotFound`.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | story | `test_derivation.py::test_overdue_payable` | class is not derived |
| FR-002 | story | `test_derivation.py::test_payable_and_receivable_share_one_rule` | the two sides disagree or the payable is absent |
| FR-003 | story | `test_derivation.py::test_overdue_payable_boundaries` | settled, undue, reversed and sales invoices are not distinguished |
| FR-004 | service | `test_derivation.py::test_overdue_payable_entry_shape` | causal values and trace keys missing |
| FR-005 | story | `test_derivation.py::test_overdue_payable_clears_through_payment` | entry persists after payment |
| FR-006 | service | `test_explanation.py::test_new_trade_classes_explanation_and_not_found_parity` | identity unknown to explanation |
| FR-007 | service | `test_derivation.py::test_overdue_payable_orders_longest_first` | order constants lack the id |
| FR-008 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-009 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| DR-001 | story | `test_overdue_payable_clears_through_payment` | nothing persists |
| DR-002 | story | `test_payable_and_receivable_share_one_rule` | a second due-date rule appears |
| DR-003 | service | `test_overdue_payable_entry_shape` | trace restates business fields |
| DR-004 | story | `test_derivation.py::test_overdue_payable_is_tenant_scoped` | cross-tenant rows leak |
| DR-005 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |
| DR-006 | review | cross-reference review over all ten classes | a pair names its sibling only once |

## Rollout and Rollback

No migration, so rollback is a plain revert. A tenant with an imported purchase ledger will
see every unpaid supplier invoice at once, exactly as the receivable did. That volume was
measured for Spec 069 and the same shape is expected, so the check is repeated on the
payable side rather than assumed to match.

## Review Risks

- **The extraction is the substantive change.** Two derivations become one parameterised
  body. If the parameterisation is wrong, both sides break together — which is the trade
  accepted for having one rule.
- **The feature is small and the specification is long.** Most of it records what was
  removed and why. A reviewer looking for code will find little; the value is in the four
  rejected conditions, which are now documented findings about the model rather than open
  ideas that will be proposed again.
- **The excluded three-way match.** A reviewer may expect it. The specification records
  precisely what the model lacks, which is what a later schema change will need as proof.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
