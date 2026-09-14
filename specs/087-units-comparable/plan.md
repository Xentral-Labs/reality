# Implementation Plan: Say When the Units Do Not Meet

**Branch**: `087-units-comparable` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One shared decision about whether two quantities can be compared, replacing three inline unit
checks that each answered it separately, and one class reporting the pairs it still declines.

No schema. The catalog gains its twenty-fourth class, and six classes stop being silently blind
where a company has already said how its units relate.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; no schema change
**Testing**: pytest business stories under `tests/operational_exceptions/`
**Project Type**: backend service consumed unchanged by Web, MCP, and Chat adapters
**Constraints**: Decimal quantities; exact conversion only; opaque IDs; strict tenant scope
**Scale/Scope**: One shared helper, three call sites replaced, one derivation

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Every figure is Evidence the tenant recorded: the quantity on a line and the relation on the item. The entry traces to the item and the lines by opaque identity | PASS |
| Reality owns operational state | Nothing gains a status; the entry is derived per read and nothing is stored | PASS |
| Proven schema only | No schema change. `purchase_unit` and `conversion_factor` exist on the Item and have since the master-data baseline | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; one shared decision answers comparability for every class that asks | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | The entry names the two units and the lines affected, so an operator can see exactly what is not being judged and why | PASS |
| Received values not recomputed | A quantity times a stated factor, at read time, stored nowhere, is the observation principle VIII allows. Prices are never converted, because dividing produces money nobody stated — that is the line this product draws and this feature keeps | PASS |
| Smallest coherent design | Three alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Convert everything, prices included.** More useful and it crosses the line: a price per box
  divided by twelve is a money figure nobody stated, and where it does not divide evenly it is
  the rounding this product was built to avoid.
- **Convert approximately and round.** The same objection with the pretence removed.
- **Report the decline per line rather than per item.** Simpler to derive and useless to act on:
  a thousand lines for one item produce a thousand entries about one missing statement.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/exceptions.py         # the shared decision, the derivation, registry, order
packages/reality-core/src/reality/catalogs.py                    # class order
packages/reality-core/config/operational_exception_catalog.yaml  # the class and its guidance
packages/reality-core/tests/operational_exceptions/              # derivation and explanation proof
docs/features/operational_exceptions.md                          # taxonomy row and the comparability rule
apps/docs/content/catalogs/exceptions.md (+ de/)                  # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                     # specification row
```

## Design

### One decision, three callers

Today `_billed_quantity`, `_credited_quantity` and `_invoice_price_differs_exceptions` each
decide comparability with their own inline `line.unit != agreed.unit`. Three copies of one rule
is how two of them come to disagree, and this feature makes the rule interesting enough that
they would.

A single helper answers it: given a line and the unit a comparison is being made in, return the
quantity expressed in that unit, or nothing. It returns nothing where the units differ and the
item states no usable relation, where the relation does not apply to this pair, and where the
conversion leaves a remainder.

The price class calls a different, deliberately dumber helper: units equal or no comparison. It
does not get the converting one, because converting a price is what this feature refuses.

### What counts as a stated relation

An Item's `conversion_factor` relates its `purchase_unit` to its `unit`. The relation is used
only for that pair and only when the factor is above zero. A line in a third unit — kilograms
on an item stocked in pieces and bought in boxes — has no stated relation and is declined.

Exactness is required in the direction the conversion runs. Ten boxes at twelve is a hundred
and twenty pieces, exactly. A hundred and seven pieces is not a number of boxes, so that pair
is declined rather than rounded.

### The class

`units_not_comparable` walks the pairs the quantity comparisons declined and reports **one entry
per item**, naming both units, how many lines are affected, and which of two things went wrong.
Per item because the missing statement is a property of the item and so is the fix; per line it
would be a wall.

The two reasons are not the same problem and the entry says which applies. *No stated relation*
is master data nobody filled in, and the exit is to fill it in. *A stated relation that does not
divide evenly* is a company that ordered ten boxes and delivered a hundred and seven pieces, and
the exit is to record the line in a unit that comes out. Telling the second one to state the
relation would be advice it has already taken.

A price comparison declined for units produces no entry at all. FR-006 refuses to convert
prices, so there is no statement that would make that comparison possible, and an entry
promising one would be a lie.

The carrier is the Item, which is already a record type. Each entry sorts on the item's
identity, which is stable, because there is no meaningful instant for "this has never been
stated".

### What does not change

Every class keeps reporting exactly what it reports today for pairs whose units already match.
The existing suites are the proof of that and are expected to pass untouched — if any of them
changes behaviour, the shared helper is wrong.

### Data and migration impact

None. No column, no revision, no backfill.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | story | `test_derivation.py::test_a_stated_conversion_lets_the_comparison_happen` | the pair is skipped |
| FR-002 | story | `test_a_stated_conversion_lets_the_comparison_happen` | a figure is invented |
| FR-003 | story | `test_derivation.py::test_an_inexact_conversion_is_declined` | a remainder is rounded |
| FR-004 | story | `test_derivation.py::test_a_useless_factor_is_no_relation` | zero is used as a factor |
| FR-005 | story | `test_derivation.py::test_a_third_unit_has_no_stated_relation` | an unrelated unit converts |
| FR-006 | story | `test_derivation.py::test_prices_are_never_converted` | a price is divided |
| FR-007 | story | `test_derivation.py::test_units_not_comparable` | class is not derived |
| FR-008 | story | `test_units_not_comparable`; `test_derivation.py::test_the_entry_says_which_of_the_two_went_wrong` | one entry per line appears; the two reasons are indistinguishable |
| FR-008a | story | `test_derivation.py::test_prices_are_never_converted` | a price decline produces an entry |
| FR-009 | service | `test_derivation.py::test_the_units_entry_exposes_full_shape` | causal values missing |
| FR-010 | story | `test_derivation.py::test_the_units_entry_clears_through_reality` | stating the relation leaves the entry |
| FR-011 | service | `test_explanation.py::test_units_class_explanation_and_not_found_parity` | identity unknown to explanation |
| FR-012 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-013 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| FR-014 | story | `test_derivation.py::test_the_units_entry_orders_deterministically` | order varies between reads |
| FR-015 | story | every existing derivation suite, unchanged | an existing class changes behaviour |
| DR-001 | review | no file under `migrations/versions/` is added | — |
| DR-002 | story | `test_the_units_entry_clears_through_reality` | something persists |
| DR-003 | unit | `test_derivation.py::test_one_decision_answers_comparability` | a second rule appears |
| DR-004 | service | `test_the_units_entry_exposes_full_shape` | trace restates business fields |
| DR-005 | story | `test_derivation.py::test_the_units_class_is_tenant_scoped` | another tenant's items are read |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no stored value changes. Rollback is a plain revert.

Two visible effects, both intended. Comparisons that were silently skipped now happen where a
company has stated the relation, so classes may report conditions that were previously
invisible. And the new class is loud on a tenant whose items carry no conversions — bounded by
items rather than lines, and saying something true that was never said before.

The demo month records no mixed units and will not change.

## Review Risks

- **The new class arrives loud.** A tenant that has never maintained conversion factors sees
  one entry per item whose lines mix units. That is the condition being reported rather than a
  defect, and it is the first class in this catalog whose subject is the company's own master
  data rather than a transaction.
- **Converting quantities is arithmetic, and somebody will read it as computing.** The
  distinction — an observation over stated facts, at read time, stored nowhere — is the one
  principle VIII draws, and the reason prices are excluded is the same principle read the other
  way. If a reviewer disagrees, the thing to argue is FR-001, not the implementation.
- **Exactness cuts both ways.** Requiring an exact conversion means a company ordering in boxes
  and delivering odd pieces gets declines instead of comparisons, and the new class will tell
  it so repeatedly. That is honest and it may be irritating.
- **Three inline checks becoming one is a behaviour change to six shipped classes.** The
  affected classes are `shipped_not_billed`, `billed_not_received`, `receipt_unbilled`,
  `returned_not_credited`, `credited_not_returned` and `invoice_price_differs`. The existing
  suites passing untouched is the evidence that nothing moved for matching units, and a reviewer
  should confirm that is what the diff shows.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
