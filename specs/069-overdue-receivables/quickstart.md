# Validation Quickstart: Overdue Receivable Visibility

## Prerequisites

- Python 3.12+ development environment
- Local PostgreSQL test service on the port used by the test configuration
- Approved Spec 069 scope decisions

Run the suite from `packages/reality-core`. In a git worktree the virtual environment
lives in the main checkout, so the worktree source has to take precedence:

```bash
PYTHONPATH=$PWD/src ../../.venv/bin/pytest
```

## 1. Consolidate the Rule Before Adding the Class

Put the due-date rule in one place and run the whole backend suite. Every previously
passing test must still pass, and the only newly passing tests may be the two that prove
the rule itself. A recovered failure anywhere else means the consolidation changed
behaviour and must not be carried into the class.

Watch for the tenant isolation catalog while doing this. A new public service function
that takes a session and a tenant must be classified there; an internal lookup should stay
private instead.

## 2. Run the Unpaid Invoice Story

Use a controlled UTC instant. Issue sales invoices dated before it with a payment term, and
compare: overdue, not yet due, due exactly at the instant, no recorded date, fully settled,
reversed, and a supplier invoice. Only the overdue unsettled sales invoice appears, and it
disappears once the remainder is paid.

Then partially settle one: pay part of it and credit part of it. The entry must report what
is still owed, not the gross amount, and must agree with the ledger's own open amount for
the same invoice.

## 3. Prove the Rule Has One Home

Ask the register and the read model for the same invoice at the same instant and compare
the due date and the days overdue. Then read the read model's source and assert it contains
no date arithmetic. The rule is only trustworthy while there is one of it.

## 4. Prove Shared Interfaces and Ordering

Compare the derivation results with the shared row contract every adapter reads, including
the new class. Read the queue twice without changing data and confirm both reads are
identical, with the overdue receivable ahead of an unmatched financial event and the
longest-overdue invoice first among receivables.

## 5. Judge the First-Deployment Volume

Seed a realistic tenant, including invoices with no payment term of their own, and read the
queue composition twice: once with the customer carrying a term and once without. An
invoice is due on its issue date only when neither it nor its customer promises a later
one, so the two readings show what the cascade is worth. The question is not whether the
class is correct but whether it drowns the queue.

## Recorded Results

| Step | Date | Result |
|---|---|---|
| 1 — consolidation is behaviour-neutral | 2026-09-04 | Pass. 11 failed, 419 passed, against 13 failed before; the only recovered failures were the two rule tests. |
| 2 — unpaid invoice story | 2026-09-04 | Pass. Boundaries, partial settlement, clearing and the supplier-invoice exclusion all proven. |
| 3 — one home for the rule | 2026-09-04 | Pass. Register and read model agree; the read model contains no date arithmetic. |
| 4 — shared interfaces and ordering | 2026-09-04 | Pass. 430 passed, 7 skipped; ruff and the spec gate green. |
| 5 — first-deployment volume | 2026-09-04 | Pass with a finding, then fixed. Demo scenarios unaffected. The first measurement found 22% of rows were invoices no operator would call late; the term cascade removed all of them and the measurement was repeated. |

### Measured on 2026-09-04

| Data | Queue total | Overdue receivable | Share |
|---|---:|---:|---:|
| `ensure_demo` — no invoice at all | 1 | 0 | 0% |
| `demo/normal_month` — the repository's own realistic month | 1 | 0 | 0% |
| Imported ledger: 200 invoices over 12 months, 80 unpaid, plus 20 issued in the last 20 days with no term | 91 | 91 | 100% |

Both demo scenarios gain nothing. `normal_month` posts its sales invoice with a future
date, so it is not late, and `ensure_demo` has no invoice at all.

The imported ledger fills the queue entirely, which is the same shape Spec 068 measured for
overdue promises. The number that mattered was inside it: **20 of the 91 rows were invoices
that carried no payment term and were therefore late on the day they were issued**, the
youngest reading `overdue by 1 day`. No operator would call an invoice issued yesterday
late.

That measurement decided T905. The rule now cascades to the party's term, and the same
ledger was measured again against the same data:

| Governing term | Queue total | Youngest row | Late only for want of a term |
|---|---:|---|---:|
| Invoice term only, fallback to issue date | 91 | `overdue by 1 day` | 20 of 20 |
| Invoice term, else the customer's term | 63 | `overdue by 2 days` | 0 of 20 |

Twenty-eight rows disappear and every remaining one is genuinely past a promised date. The
youngest is two days late under a thirty-day term, which is a real finding rather than an
artefact of a missing field. The fallback survives only where neither the invoice nor its
customer promises anything, which is what a last resort should look like.

## Findings Worth Keeping

Making a helper public has a governance cost. `payment_terms_by_id` as a public service
function broke eight tests at once — `tenant_isolation/test_families.py` and the catalog
tests — with `Tenant isolation catalog drift: missing=[...]`. Every public tenant-scoped
operation must be classified in `tenant_isolation_catalog.yaml`. The fix was not to add an
entry but to keep the lookup private: it loads a dictionary, it is not an operation an
adapter should reach. The three genuinely reusable names take no session and no tenant, and
the registry did not object to them.

The class consumes `aging_register` directly rather than deriving a due date from its
inputs. That is the strongest available expression of the single-rule requirement: there is
no arithmetic in the exception derivation at all, only a filter and a presentation.

The Inspector shows no metric for this class, deliberately. Its one metric is keyed on the
reservation-shortfall cause, and this class has no cause, so the outstanding amount travels
in the impact line and the causal values instead. Rendering a metric per numeric causal
value would be a better Inspector, and it is a presentation change rather than part of this
feature.
