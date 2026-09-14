# Implementation Plan: One Friday, Forty Payments

**Branch**: `098-a-payment-run` | **Date**: 2026-09-07 | **Spec**: [spec.md](./spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

One shared rule for what is payable, a preview that assembles what is already derived and writes
nothing, and one operation that pays a confirmed list in a single transaction. No schema, no
arithmetic, no new class.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, PyYAML
**Storage**: PostgreSQL; **no migration**
**Testing**: pytest, `tests/test_payment_runs.py` and the existing finance suites
**Project Type**: backend service consumed by Web, MCP, CLI and Chat adapters
**Constraints**: One transaction per run; strict tenant scope; no derived money
**Scale/Scope**: One rule, two operations, four surfaces, one catalog guidance correction

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | A run pays supplier invoices, which are Evidence, and produces the same payment documents and postings a single payment produces | PASS |
| Reality owns operational state | What is payable is derived per read from the register the product already owns; the run stores nothing new about an invoice | PASS |
| Proven schema only | No migration. Every figure, relation and event type this needs already exists | PASS |
| Tenant + shared service boundaries | Every query filters `tenant_id`; one payable rule serves the preview, the run and the duplicate class | PASS |
| Spec/test traceability | Every FR and DR maps to a named test below | PASS |
| Explainable web behavior | The preview says what it proposes, what it withheld and why, and names the rate without applying it | PASS |
| Received values not recomputed | **The centre of this feature.** Every amount paid is stated by the caller. The preview reports what is open and the rate a term states, and never multiplies one by the other | PASS |
| Smallest coherent design | Four alternatives rejected below | PASS |

Planning MUST stop while any row is FAIL or unresolved.

### Simpler alternatives considered

- **Let the run compute the discounted amount.** This is what an ERP payment run does and it is
  the single largest source of derived money in one. `2%` of `1,234.56` is `24.6912`, which has
  to be rounded, and the rounded figure becomes what a supplier is told they were paid. Principle
  VIII exists for exactly this. The preview names the rate; a person states the amount.
- **Derive the invoices to pay instead of naming them.** Then the run pays something nobody
  looked at, and the preview becomes decoration. The confirmation only means something if what is
  confirmed is what runs.
- **A payment-run document, with the payments posted against it.** It would put a record in the
  ledger for something that is not a financial event. A run is a decision about payments, not a
  payment; the product already has a place for decisions, and it is the business event.
- **A durable per-invoice payment block.** It is the honest answer to "do not pay this one" and
  it needs a schema change, a lifecycle, a release operation and a register. Excluding an invoice
  by not naming it costs one omission per run and no schema, and the invoice reappearing in the
  next preview is the queue behaving correctly. Named as a limit rather than built.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py        # the payable rule, the preview, the run
packages/reality-core/src/reality/services/exceptions.py  # the duplicate class consumes the shared rule
packages/reality-core/config/command_catalog.yaml         # two commands
packages/reality-core/config/tenant_isolation_catalog.yaml
packages/reality-core/config/business_event_catalog.yaml  # payments.run
packages/reality-core/config/operational_exception_catalog.yaml  # the discount guidance names the run
packages/reality-core/src/reality/tools/application.py, mcp/catalog.py, web/api.py
packages/reality-core/tests/test_payment_runs.py          # new
docs/features/procure_to_pay.md, docs/features/operational_exceptions.md
apps/docs/content/catalogs/ (+ de/), docs/SPEC_COVERAGE_MATRIX.md
```

## Design

### One rule for what is payable

`payable_supplier_invoices(session, tenant_id, as_of=…)` returns the register rows for every
supplier invoice a run may pay, and, beside it, every row it withheld with the reason. Payable
means: a supplier invoice, not reversed, with something open, and not reported as a duplicate.

The preview asks it. The run asks it. Nothing else decides, and a test asserts nothing else
computes it. This is the fifth derived figure in this line of work that had to be single-sourced —
unit comparability, learned thresholds, the date in force, the quantity in force, and now what is
payable — and by now the rule is written once before either caller exists.

### The duplicate rule moves down, not sideways

`_duplicate_supplier_invoice_exceptions` groups supplier invoices by party and by the number
their supplier put on them, ignoring case and surrounding spaces, and reports every document
after the first. A run needs exactly that set, and copying it would give the product two answers
to "is this a duplicate".

So the grouping moves into `core.duplicate_supplier_invoices()` — returning each duplicate
paired with the document it duplicates — and the exception class becomes its second consumer. The direction matters: `exceptions` already depends on `core` and `core` does not
depend on `exceptions`, so the rule moves down the stack rather than across it.

### The preview assembles, it does not calculate

Every figure comes from `aging_register`: what is open, the due date, the discount date and the
term. That is deliberate under DR-003 — the preview, the aging register and the operational
exception queue must never be able to disagree about what an invoice owes.

It proposes an invoice when its due date falls on or before the stated day, **or** when its
early-payment window has not closed yet. The second half is why the discount class named a
payment run in its guidance: an invoice not yet due can still be the one worth paying now.

The window is measured against today rather than against the stated day, deliberately. An invoice
whose window shuts tomorrow is the most urgent line in the proposal; testing it against a day a
week out would drop it from a run made this afternoon.

Ordering is by the day the money is needed — the discount deadline where there is one, otherwise
the due date — and then by identity, so two identical previews of an unchanged tenant are
identical.

It names the rate and the deadline. It never names what the discount is worth. That sentence is
already in the discount class's own description and it is the same sentence here.

### The run pays what it was given

`execute_payment_run(payments=[{invoice_id, amount}], currency, expected_total, reason)`.

Everything it refuses, it refuses before it writes: an empty list, a missing reason, an invoice
named twice, an invoice that is not payable, an amount above what the invoice has open, a total
that does not match the sum, a currency that does not match an invoice's. Then it posts every
payment through `post_supplier_payment(_commit=False)` — the same operation a single payment
uses, so a payment in a run is the same posting as a payment made alone — emits one
`payments.run` event, and commits once.

A failure anywhere rolls the whole thing back. That is the reason the operation exists: the
alternative is a Friday where nineteen payments went out and twenty-one did not, and somebody has
to work out which.

### Why the confirmation figure is a total

Spec 085 confirmed a count, because a count was what the person had looked at. Here a person
approves an amount of money, and the list is usually built by a client from the preview. Every
line can be right and the sum still be wrong. The total is what was approved, so the total is
what is checked.

### One currency

A total in two currencies is not a total. Converting would guess a rate nobody agreed, which is
the rule Spec 076 applied to units and Spec 078 to credit limits. A company paying in two
currencies runs two runs.

### What this deliberately leaves alone

There is no durable way to say "never pay this invoice". Holding one back means leaving it out,
and it appears again in the next preview. For an invoice under dispute that is mildly annoying
and strictly correct — it is unpaid, and this queue reports what is unresolved until somebody
resolves it. The alternative is a schema change with a lifecycle and a release path, which is a
separable feature.

### Data and migration impact

None. No table, no column, no revision. `payments.run` is a new event type, which the event
catalog already models as configuration.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `test_payment_runs.py::test_one_rule_decides_what_is_payable` | a second rule appears |
| FR-002 | service | `test_payment_runs.py::test_what_is_not_payable_and_why` | a duplicate is proposed |
| FR-003 | service | `test_payment_runs.py::test_the_preview_writes_nothing` | the preview writes |
| FR-004 | service | `test_payment_runs.py::test_the_preview_proposes_what_is_due_and_what_is_discountable` | the window is ignored |
| FR-005 | service | `test_payment_runs.py::test_the_discount_is_named_never_applied` | a discounted amount appears |
| FR-006 | service | `test_payment_runs.py::test_what_is_not_payable_and_why` | withheld rows are silent |
| FR-007 | service | `test_payment_runs.py::test_the_preview_totals_per_supplier_and_overall` | no supplier grouping |
| FR-008 | service | `test_payment_runs.py::test_a_run_pays_exactly_what_it_was_given` | an amount is derived |
| FR-009 | service | `test_payment_runs.py::test_a_run_refuses` | a refusal is accepted |
| FR-010 | service | `test_payment_runs.py::test_a_run_is_one_currency` | a mixed run is accepted |
| FR-011 | service | `test_payment_runs.py::test_a_failed_run_leaves_nothing_behind` | payments survive a failure |
| FR-012 | service | `test_payment_runs.py::test_a_run_is_recorded_as_one_decision` | no event |
| FR-013 | service | `test_payment_runs.py::test_a_payment_in_a_run_is_an_ordinary_payment` | the postings differ |
| FR-014 | unit | the catalog drift gates and `test_docs_contract` | guidance names nothing |
| FR-015 | story | every existing suite, unchanged | an existing behaviour moves |
| DR-001 | review | no migration added | — |
| DR-002 | unit | `test_payment_runs.py::test_the_duplicate_rule_has_one_home` | two answers exist |
| DR-003 | service | `test_payment_runs.py::test_the_preview_reads_the_register` | a figure is computed twice |
| DR-004 | service | `test_payment_runs.py::test_a_run_is_tenant_scoped` | another tenant is reachable |
| DR-005 | unit | `test_coverage.py` closed registry test | passes unchanged |
| DR-006 | service | `test_the_discount_is_named_never_applied` | money was derived |
| DR-007 | unit | `test_application_catalog.py` reachability gate | an operation is undeclared |

Every negative test carries a positive control in the same test.

## Rollout and Rollback

No migration and no change to any existing operation. Both new operations are additive: a tenant
that never calls them behaves exactly as it does today. Rollback is removing the two commands.

The demo month runs no payment run and its queue is unchanged.

## Review Risks

- **The run refuses to pay an invoice reported as a duplicate.** This is the one place the
  feature refuses on a derived condition rather than reporting it, which is unusual for this
  product. The argument is that paying a duplicate is unrecoverable, the class is the only
  payable condition marked high, and it has a clearing path — reverse the wrong posting or
  confirm the numbers differ — so nobody is trapped. A reviewer who disagrees is arguing for a
  warning in the preview and no refusal in the run.
- **Refusing to compute the discount will look like a missing feature.** It is the feature. An
  ERP payment run's discount arithmetic is the largest source of money nobody agreed to, and
  Principle VIII was written before this specification. The preview gives a person everything
  they need to state the amount themselves.
- **No durable per-invoice block.** The largest thing this does not do, argued in the design and
  named in the specification.
- **One run, one transaction, forty postings.** A large run holds a transaction open longer than
  any other operation in the product except the stale-promise closure, which has the same shape.
  If that becomes a problem it is a problem about size, and the answer is smaller runs rather
  than partial ones.

## Complexity Tracking

No Constitution exception is claimed. There is no schema change, no new entity, no new exception
class, and no new derived value.
