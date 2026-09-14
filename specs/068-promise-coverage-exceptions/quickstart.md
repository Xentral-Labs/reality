# Validation Quickstart: Customer Promise and Stock Coverage Exceptions

## Prerequisites

- Python 3.12+ development environment
- Local PostgreSQL test service on the port used by the test configuration
- Approved Spec 068 scope decisions and the relaxed catalog cause vocabulary

Run the focused suite from `packages/reality-core`. In a git worktree the virtual
environment lives in the main checkout, so the worktree source has to take precedence:

```bash
PYTHONPATH=$PWD/src ../../.venv/bin/pytest tests/operational_exceptions
```

## 1. Prove the Catalog Gate Alone

Relax the cause vocabulary before declaring any class and run the whole backend suite.
Every previously passing test must still pass and the production catalog must still load.
A recovered failure other than the vocabulary test itself means the change was not a
no-op and must not be carried into an activation.

## 2. Activate One Class at a Time

Register the derivation, place the class in both order constants, and declare it in the
catalog in a single step. Loading the catalog with the constant and the YAML out of step
raises, so a partial activation fails every test that touches the catalog rather than only
the new ones.

## 3. Run the Late Promise Story

Use a controlled UTC instant. Compare an open customer-delivery commitment with an absent
due date, a future due date, a due date equal to the instant, and a past due date. Only
the past one appears, and it disappears once the outstanding quantity ships.

Then make the same promise both late and short of reservation. Exactly one entry must
exist for that commitment: the overdue class, carrying `insufficient_reservation` as its
cause, with a queue row that names the overdue remainder and the unreserved portion of it.
No at-risk row may exist for the same record.

## 4. Run the Unbacked Reservation Story

Reserve an item fully against its stock and confirm the reserve operation cannot
over-allocate — the shortage it reports is zero and no exception exists. Then remove stock
with an adjustment. The item-level entry appears with observed stock, reserved quantity,
the shortfall, and the number of competing promises, while the commitment itself still
reports no risk. This is the point of the class: nothing else in the queue sees the loss.

Walk the boundary: receive stock back to equality, then to sufficiency, then transfer the
stock to another location. None of those produce an entry, because coverage is judged per
item across the tenant. An item reserved with no recorded movement at all does produce
one.

## 5. Prove Shared Interfaces and Ordering

Compare the derivation results with the shared row contract every adapter reads. The class
identifiers, causes, record types, causal values, and traces must agree, and no
presentation adapter may contain a class predicate. Read the queue twice without changing
data and confirm both reads are identical, with an already-late promise ahead of a merely
risky one.

## Recorded Results

| Step | Date | Result |
|---|---|---|
| 1 — catalog gate no-op | 2026-09-04 | Pass. 16 failed, 403 passed; the only recovered failure was the vocabulary test itself. |
| 2 — overdue class activation | 2026-09-04 | Pass. 12 failed, 407 passed; all remaining failures need the second class or its seven-class list. |
| 3 — late promise story | 2026-09-04 | Pass. Boundaries, clearing, single-entry exclusivity, cause and impact all proven. |
| 4 — unbacked reservation story | 2026-09-04 | Pass. Boundary walk, clearing, opaque references and agreement with the Inventory view all proven. |
| 5 — shared interfaces and ordering | 2026-09-04 | Pass. 420 passed, 7 skipped; ruff and the spec gate green. |
| 6 — first-deployment volume | 2026-09-04 | Pass with a finding. Demo scenarios unaffected; an imported legacy book fills the queue entirely, and the impact clause was repeating itself on the commonest row. |

## 6. Judge the First-Deployment Volume

Seed a throwaway database with the demo scenarios and with an imported order book whose
source never closed finished orders, then read the queue composition for each. The
question is not whether the class is correct but whether it drowns the queue on real data.

Measured on 2026-09-04 against `473190e`:

| Data | Queue total | Overdue outgoing | Share |
|---|---:|---:|---:|
| `ensure_demo` — one order, dates relative to today | 1 | 0 | 0% |
| `demo/normal_month` — the repository's own realistic month | 1 | 0 | 0% |
| Imported book: 60 orders over 12 months, 12 never closed | 12 | 12 | 100% |
| Imported book: 300 orders over 24 months, 30 never closed | 30 | 30 | 100% |

Both demo scenarios gain nothing, so onboarding and demonstrations are unaffected. On an
imported book the count equals the number of stale open orders exactly — one row per
promise, no multiplication, no interaction with other classes — but it then makes up the
entire queue. Every row carries the same class and the same severity, so neither ordering
nor severity can triage it and only `due_at` separates the rows, oldest first. The useful
action there is closing those orders at the source, and the product offers nothing to do
that in bulk. The decision to treat the backlog as a true finding stands; the first look
into the queue after a legacy import is nonetheless a wall of dead promises.

The synthetic book makes its own count trivially predictable. What the measurement is
worth is the absence of side effects, not the number.

## Findings Worth Keeping

Two pre-existing tests pinned a due date that wall-clock time has since passed. They
assert at-risk behaviour, which now only holds while a promise is not yet late, so each
was given its own explicit instant rather than relying on today's date. This was a latent
fragility in those tests, surfaced rather than caused by this feature.

The Inspector route carried a class predicate: the "Uncovered" metric was shown only for
`outgoing_commitment_at_risk`. Left alone, an overdue promise with an unreserved remainder
would have lost that metric even though the shortfall is now one of its causes. The route
keys on the cause instead, which is what a cause vocabulary is for, and the frontend needs
no change at all — `apps/web` and `provider-site` are byte-identical to `main`.

The impact clause repeated itself on the commonest row. A promise with nothing reserved
read `7 remain overdue, 7 of them unreserved`, saying the same quantity twice, and that is
exactly the row an imported order book produces most. The clause is now appended only
where it carries a value the class condition does not already state. The cause stays
attached either way, so nothing is lost from the explanation.

Quantity formatting follows the stored scale, so the same row reads `7 remain overdue`
from an in-session value and `7.0000 remain overdue` once it has come back from the
database. That is pre-existing behaviour shared by every class — `outgoing_commitment_at_risk`
has always read `10.0000 remains unreserved` — and belongs to a separate change if it is
worth making at all.

The catalog reference generator emits unaligned Markdown while the committed pages are
formatted. Running it without `npm run format` in `apps/docs` produces a whitespace-only
diff across every catalog page — roughly 1,300 lines of noise around 46 real ones. The
instruction line inside the generated pages does not mention the formatting pass.
