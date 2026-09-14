# Validation Quickstart: Overdue Payables

## Prerequisites

- Python 3.12+ development environment
- Local PostgreSQL test service on the port used by the test configuration
- Approved Spec 074 scope, including the three conditions it deliberately does not deliver

Run the suite from `packages/reality-core`. In a git worktree the virtual environment lives
in the main checkout, so the worktree source has to take precedence:

```bash
PYTHONPATH=$PWD/src ../../.venv/bin/pytest
```

## 1. Extract Before Adding

Parameterise the open-item exception and run the whole backend suite before the payable
consumes it. Every previously passing test must still pass and nothing may turn green. If
the receivable changes behaviour here, the parameterisation is wrong, and both sides would
have been wrong together.

## 2. Run the Unpaid Supplier Invoice Story

Use a controlled instant. Post supplier invoices dated before it with a payment term and
compare: overdue, not yet due, no readable date, fully paid, reversed. Only the overdue
unsettled one appears. Put a sales invoice in the same state beside them and confirm it
stays a receivable.

## 3. Prove Both Sides Mean the Same Thing

Give a customer and a supplier the same payment term, issue one invoice on each side with no
term of its own, and confirm both derive the same due date and the same days overdue. That
is the whole point of sharing the rule: the cascade to the party must behave identically or
"due" means two different things in one queue.

## 4. Prove Clearing, Ordering and Isolation

Payment must remove the entry on the next read with nothing persisted. Two overdue payables
must appear longest-overdue first, identically across repeated reads. One tenant's invoices
must never appear in another's queue.

## 5. Prove the Catalog and the Pairs

The class must carry the description, owner and clearing path Spec 071 made mandatory, and
must name both the receivable and the overdue supplier delivery, with those two amended to
name it back. Re-run the cross-reference review over all ten classes afterwards.

## Recorded Results

| Step | Date | Result |
|---|---|---|
| 1 — extraction is behaviour-neutral | 2026-09-04 | Pass. |
| 2 — unpaid supplier invoice story | 2026-09-04 | Pass. Boundaries, reversal and the sales-invoice separation all proven. |
| 3 — both sides share one rule | 2026-09-04 | Pass. Identical due date and days overdue from a party-level term on each side. |
| 4 — clearing, ordering, isolation | 2026-09-04 | Pass. |
| 5 — catalog and pairs | 2026-09-04 | Pass. Six mutual pairs; only `unexplained_movement` stands alone. |
| 6 — first-deployment volume | 2026-09-04 | Pass. Demo scenarios unaffected; an imported purchase ledger produces 63 entries, the same count the receivable produced for the same data shape, with no false positive from the term cascade. |

Full suite after implementation: 500 passed, 7 skipped.

### Measured on 2026-09-04

| Data | Queue total | Overdue payable | Youngest payable |
|---|---:|---:|---|
| `ensure_demo` — no supplier invoice at all | 1 | 0 | — |
| `demo/normal_month` | 1 | 0 | — |
| Imported: 200 purchase invoices over 12 months, 80 unpaid, plus 20 recent without their own term | 246 | 63 | `overdue by 2 days` |

Both demo scenarios gain nothing. The imported ledger produces sixty-three payables — the
same count Spec 069 measured on the receivable side for the same data shape, which is what
sharing one rule is supposed to produce and is now observed rather than assumed. None of
the twenty recent invoices without a term of their own appears, because the supplier carries
one: the cascade behaves identically on both sides.

## Findings Worth Keeping

**Three of the four conditions proposed for this feature cannot exist.** That is the durable
result, and it is worth more than the class that survived.

Goods moved beyond a commitment was specified, implemented and tested before the write path
was checked. `record_movement` refuses a movement beyond the commitment's open quantity, no
operation reduces a commitment's quantity afterwards, and a correction carries no commitment
reference at all. The `max(0, promised − moved)` that looked like it was hiding the case is
hiding nothing.

Negative stock is refused twice over: outbound movements beyond the stock at their location,
and corrections whose compensation would remove stock later movements depend on.

The full three-way match between order, goods and invoice cannot be derived at all, because
no reference exists from an invoice to the order it invoices and invoices are never created
from a source record.

**The pattern is worth stating.** Reality prevents at write time nearly every inconsistency
an ERP would normally detect afterwards. Real exceptions therefore come from only three
places: time passing, something arriving or failing to arrive from outside, and state
changing after a check has already passed. `reservation_exceeds_stock` survived earlier
scrutiny precisely because it belongs to the third group — stock can leave after the
reservation was made. Over-delivery, negative stock and over-reservation have no such later
route, which is why none of them exists.

A queue that stays small is not a queue that is missing conditions.
