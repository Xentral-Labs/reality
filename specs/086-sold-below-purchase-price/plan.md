# Implementation Plan: Sold for Less Than It Costs to Buy

**Branch**: `086-sold-below-purchase-price` | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One derivation comparing two figures somebody stated: the price a sales order line agreed, and
the purchase price the company had standing for that item at the time. No schema, no cost
model, no valuation method.

The catalog gains its twenty-third class. The feature exists because an assumption turned out
to be wrong — that margin needs a cost basis Reality does not hold.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML for the closed catalog
**Storage**: PostgreSQL; no schema change
**Testing**: pytest business stories under `tests/operational_exceptions/`
**Project Type**: backend service consumed unchanged by Web, MCP, and Chat adapters
**Constraints**: Decimal money; opaque IDs; strict tenant scope
**Scale/Scope**: One derivation, one price lookup, no transport change

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Both figures are Evidence the tenant recorded — an agreed line and a price list entry — and the trace reaches the line, its document and the SourceRecord by opaque identity | PASS |
| Reality owns operational state | Nothing gains a status; the entry is derived per read and nothing is stored | PASS |
| Proven schema only | No schema change. Sales order lines, purchase price lists and their entries all exist and are all first-class today | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`, including the price-list lookup | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | The entry returns both prices and the shortfall, so a judgement can be checked rather than believed | PASS |
| Received values not recomputed | This is the principle that makes the feature possible. Both figures were stated by a person; a cost model would have made Reality the author of a number nobody stated, and was rejected for exactly that reason | PASS |
| Smallest coherent design | Three alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Derive a cost from receipts.** The assumed shape of this feature, and the reason it stayed
  unbuilt. It needs a valuation method — which receipt did this sale consume — and Reality
  would be choosing one on a company's behalf and then presenting the result as fact.
- **Compare against a supplier-specific purchase price.** More precise about one negotiation
  and wrong about the question: what a sales price should be judged against is what the company
  says the item costs it, not what one supplier happened to charge.
- **Report it on the invoice line instead.** The invoice records a decision already made. The
  order line is where somebody chose the price and where somebody can still change it.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/exceptions.py         # the derivation, registry, order
packages/reality-core/src/reality/catalogs.py                    # class order
packages/reality-core/config/operational_exception_catalog.yaml  # the class and its guidance
packages/reality-core/tests/operational_exceptions/              # derivation and explanation proof
docs/features/operational_exceptions.md                          # taxonomy row
apps/docs/content/catalogs/exceptions.md (+ de/)                  # generated, regenerated, formatted
docs/SPEC_COVERAGE_MATRIX.md                                     # specification row
```

**Files/layers affected**: the exception service and the catalog. No model, no migration, no
transport, no frontend.

## Design

### The standing purchase price

A small lookup answers one narrow question: what does the default purchase price list say this
item costs, in this currency and unit, at this moment, for this quantity.

Only the default list is read, and only while it is active: a list somebody has retired is not
a standing price. A quantity break is applied the way the resolver applies one — the highest
break at or below the line's quantity — and where none applies there is no standing price and
nothing to compare.

It is deliberately not `resolve_price`. That function answers "what price applies for this
party", walks party and group links, and needs a party to walk them with — and the party a
sales line names is a customer, not a supplier. Passing one in to reach the default list would
be inventing a relationship to satisfy a signature. The narrow lookup uses the same validity
window and the same quantity-break ordering, and says in its docstring that it answers a
smaller question than the resolver does.

### The comparison

`_sold_below_purchase_price_exceptions` walks sales order lines, resolves the standing purchase
price at the line's own effective instant, and reports where the agreed price is lower.

Four silences, each of which is a rule rather than an omission: no purchase price standing, a
currency or unit that differs, a line with no item, and a line agreed at zero. The last is the
one worth arguing about — a sample or a replacement is priced at nothing on purpose, and
reporting it would put every goodwill gesture in the queue.

Selling at exactly the purchase price is not reported either. It is a thin deal, and thin is a
decision.

### Identity, ordering and guidance

The identity is `exc__sold_below_purchase_price__{line_id}`. It sorts beside the other pricing
class, and each entry sorts on the line's own effective instant so the longest-standing comes
first.

Spec 071's cross-reference rule applies. This and `invoice_price_differs` are the two things
that can be wrong about a price and must name each other: one asks whether the invoice matches
the agreement, the other whether the agreement was sound.

The guidance carries the limitation rather than hiding it: this is an agreed sales price
against an agreed purchase price, not accounting margin, and it says so where an operator reads
it.

### Data and migration impact

None. No column, no revision, no backfill.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | story | `test_derivation.py::test_sold_below_purchase_price` | class is not derived |
| FR-002 | story | `test_sold_below_purchase_price` | a figure is adjusted |
| FR-003 | story | `test_derivation.py::test_the_price_standing_when_it_was_agreed_is_used` | today's price judges an old sale |
| FR-004 | story | `test_derivation.py::test_without_a_purchase_price_nothing_is_reported` | a figure is invented |
| FR-005 | story | `test_sold_below_purchase_price` | selling at cost is reported |
| FR-006 | story | `test_derivation.py::test_a_line_agreed_at_zero_is_a_decision` | a sample is reported |
| FR-007 | story | `test_derivation.py::test_only_sales_lines_are_judged` | a purchase line is reported |
| FR-008 | story | `test_derivation.py::test_a_different_currency_or_unit_is_not_compared` | figures are converted |
| FR-009 | story | `test_only_sales_lines_are_judged` | a freight line is reported |
| FR-010 | service | `test_derivation.py::test_the_pricing_entry_exposes_full_shape` | causal values missing |
| FR-011 | service | `test_the_pricing_entry_exposes_full_shape` | trace keys missing |
| FR-012 | story | `test_derivation.py::test_the_pricing_entry_clears_through_reality` | the entry persists after correction |
| FR-013 | service | `test_explanation.py::test_pricing_class_explanation_and_not_found_parity` | identity unknown to explanation |
| FR-014 | unit | `test_coverage.py` closed registry and guidance tests | registry drift; missing guidance |
| FR-015 | adapter | `test_explanation.py::test_shared_consumer_parity_includes_new_classes` | adapters see fewer classes |
| FR-016 | story | `test_derivation.py::test_the_pricing_entry_orders_longest_first` | order varies between reads |
| DR-001 | review | no file under `migrations/versions/` is added | — |
| DR-002 | story | `test_the_pricing_entry_clears_through_reality` | something persists |
| DR-003 | story | `test_sold_below_purchase_price` | a figure is computed |
| DR-004 | service | `test_the_pricing_entry_exposes_full_shape` | trace restates business fields |
| DR-005 | story | `test_derivation.py::test_the_pricing_class_is_tenant_scoped` | another tenant's price list is read |
| DR-006 | unit | `test_coverage.py::test_catalog_rejects_cause_vocabulary_drift` | passes unchanged |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no stored value changes. Rollback is a plain revert.

The demo month keeps no purchase price list, so the class is silent there and
`test_the_month_ends_with_exactly_these_exceptions` will not change. That is correct behaviour
and a weak test of it, and the quickstart says so.

## Review Risks

- **Silent for most companies.** The class fires only where a default purchase price list is
  maintained, and many businesses will not keep one. This is the honest shape of a feature
  built from received values, and it means the class may deliver nothing for a long time.
- **It understates.** Freight, duty and handling are not in the purchase price, so a line
  agreed slightly above it may still lose money and stays silent. Understating is the safer
  direction and it is still a gap between the class's name and what it can see.
- **A default list is a blunt instrument.** A company buying the same item from two suppliers
  at very different prices has one default that describes neither well, and every sale is
  judged against it. The alternative — supplier-specific prices — answers a different question,
  so this is a limit rather than a fix waiting to happen.
- **Zero is excluded on judgement.** A line agreed at zero is treated as a decision. A company
  that habitually zero-rates lines by mistake would see nothing, and the rule to revisit is
  FR-006.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
