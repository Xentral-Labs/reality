# Verification

## What was measured against
A copy of the local development database (866 MB, 37,311 documents) taken with
`pg_dump` and migrated to head, so before and after ran on identical rows. The company
used is the largest one present: 10,233 documents and 13,590 ledger entries. Both sides
were `ANALYZE`d. The machine was not idle — a container stack and other work were
running — so the runs were interleaved (baseline, change, baseline, change, baseline,
change) and the best of three taken for each side. The ratios were stable across all
three rounds; the absolute milliseconds are indicative, the ratios are not.

## Answers are unchanged
Seventeen questions covering per-party filtered balances, whole-company customer and
supplier balances, open items by settlement status, open items filtered to each of four
months, stock detail by location and unit, current stock positions, invoiced amount by
month and order intake by customer were run on both sides and their full result sets
compared, not just their row counts.

    diff parity_before.json parity_after.json  →  no difference
    17 questions, 104 result rows, 0 refusals, byte-identical

## What it costs now

| Question | Before | After | Statements |
|---|---|---|---|
| Open items of one month | 531 ms | 5 ms | 13 → 8 |
| Invoices of one month | 11 ms | 1 ms | 1 → 1 |
| Balances of one customer | 738 ms | 191 ms | 25 → 26 |
| Invoiced amount by month | 9 ms | 3 ms | 1 → 1 |
| Balances, whole company | 763 ms | 753 ms | 25 → 25 |
| Order intake by customer | 7 ms | 6 ms | 1 → 1 |
| Stock detail by location | 7 ms | 7 ms | 15 → 15 |

The one-month open-item question is the shape the registers ask most and the one that
was worst: it derived the whole company's aging register and then discarded almost all
of it. The extra statement in the filtered balance row is the identity query itself,
which costs one indexed read and saves the derivation most of its input.

The unfiltered whole-company questions are unchanged by design. Nothing in them narrows,
so `reachable_identities` declines and the derivation reads the company as before. What
remains there is the input-bound counts and the JSON round trip, not the filter.

The date column accounts for the two plain-path improvements: the compiler no longer
rebuilds a date per row out of `substr`, `make_date` and a validity cascade, and a period
filter can use an index. The pre-existing `ix_document_tenant_date` became a date index
rather than a text one as a side effect of the same change.

## The migration on real data
Applied to the 866 MB copy in one run. Of 37,311 documents, 6 became NULL, and all 6
already held the empty string; no row carried a day that was lost. The round-trip check
did its job: `to_date` answers 2026-03-02 for 2026-02-30 without complaint, and the
migration refuses to invent that day.

## Every template, against the ceiling
All twenty-one declared templates were executed against the same company. Worst
statement count 25, against a declared ceiling of 40 — sixty per cent headroom, so the
alarm cannot fire on a question the model already offers:

    ordinary paths (6 templates)            1 statement
    stock_by_article, reserved, shortages   9
    customer/supplier outstanding, overdue  13
    stock detail by location / lot / serial 15
    balance history (with a snapshot date)  18
    customer / supplier balance             25

The three history templates refuse without a snapshot date, as spec 232 requires; given
one they run at 15 to 18.

## The migration reverses
On the same 866 MB copy, `alembic downgrade 0062` then `upgrade head`:

    date  →  character varying, 6 rows back to ''   →  date, 6 rows NULL of 37,311

The six rows are the same six throughout. Nothing else in the table moves, so the
column change can be taken back on a running database.

## The contract this replaced
Three tests recorded that any text could be stored in `document_date` and that each
reader would decline to interpret it: `tests/test_pricing.py` kept a period label
verbatim, `tests/test_ledger.py` passed `"not-a-date"`, and
`tests/operational_exceptions/test_derivation.py` passed `"whenever"`. All three now
record the rule that replaced it — the write is refused, naming the expected format —
and each keeps its positive control, so a document stating no date is still reported as
unknown rather than as an error. The full suite found these three and nothing else in
that class.

## Checks
- 269 web contracts pass; the wire format is unchanged, so no frontend change was needed.
- All 257 reporting-graph and analysis backend tests pass, including the six new cost
  regressions and the rewritten impossible-day test.
- Ruff check clean across `packages/reality-core`; the files this feature touches are
  `ruff format` clean.
- Spec policy passes. The generated tool-usage reference was regenerated and formatted;
  its only change is the column's type and nullability.
- Full backend suite: see the run recorded below.

## What this does not fix
Push-down cannot help a question that narrows nothing, which is exactly what the
unfiltered register pages ask. Their cost still sits in the canonical derivation and its
JSON round trip, and the input caps still refuse on the company's total size rather than
on the narrowed set — deliberately, because the cap guards what the service materializes
and loosening it needs its own evidence.

The sharing of one canonical read between two positions is narrow by construction: no
declared edge leads from one derived node to another, so only an existence test walked
backwards reaches two in one path. The assessment that prompted this work overstated
that case; the machinery is kept because it is small and correct, not because it is hot.
