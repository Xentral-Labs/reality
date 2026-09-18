# Research

Measurements taken 2026-09-18 against a `pg_dump` copy of the local development database
(866 MB, 37,311 documents) migrated to head. The company used throughout is the largest
available: 10,233 documents, of which 3,430 are finance documents, and 13,590 ledger
entries. Best of three runs each; the machine was not idle, so ratios are the evidence
and absolute milliseconds are indicative.

## Where `financial_open_items` spends 473 ms

| | |
|---|---|
| total | 473 ms |
| of which SQL, 10 statements transferring ~20,000 rows | 279 ms |
| of which Python | 195 ms (41 %) |
| per finance document | 138 µs |

For comparison, on the same company and the same rows:

| | |
|---|---|
| handing the finished rows back to PostgreSQL as JSONB | 1 ms |
| one plain SQL aggregate over `document` | 1 ms |

The JSON round trip is not where the cost is. The cost is that the company's finance
history becomes Python objects.

## The cost, measured at the sizes that matter

The section above profiles one company that happened to exist. These are runs of the
repository's own fixture at the full profile, best of three samples each, statistics
analysed, same code and same host for both sizes. `financial_count` now scales with the
profile: a company with 10,000 orders has 10,000 invoices, where the fixture used to
build 120 of them regardless.

| Derivation | 10,000 | 20,000 | factor | statements |
|---|---:|---:|---:|---:|
| `financial_open_items` | 1,320 ms | 2,726 ms | 2.1× | 8 |
| `aging_register` | 1,315 ms | 3,033 ms | 2.3× | 9 |
| `party_balance_rows.customer` | 1,647 ms | 4,141 ms | 2.5× | 13 |
| `party_balance_rows.supplier` | 1,151 ms | 3,006 ms | 2.6× | 13 |
| `inventory_rows` | 9 ms | 31 ms | 3.5× | 4 |
| `inventory_detail_rows` | 8 ms | 19 ms | 2.3× | 7 |

Doubling the company roughly doubles the cost, a little more than doubles it in most
rows: 132 → 136 µs per finance document for open items, 165 → 207 µs for customer
balances. The statement counts do not move, so this is not a query issued per row; it is
the volume each of those eight to thirteen statements carries into the process.

**At the 20,000 cap where analysis refuses today, every finance derivation costs between
2.7 and 4.1 seconds.** Extrapolating the measured rate, the 30-second statement deadline
arrives somewhere between 150,000 and 200,000 finance documents — which spec 181's target
of 100 to 1,000 orders a day reaches inside a year.

Evidence: [`specs/033-large-tenant-register-benchmark/evidence/benchmark-result.json`]
(../033-large-tenant-register-benchmark/evidence/benchmark-result.json) for 10,000 and
[`evidence/derivation-cost-20000.json`](evidence/derivation-cost-20000.json) for 20,000.

### Two corrections this measurement forced

The first draft of this note extrapolated 130 µs per finance document from a company of
3,430 of them and put a million documents at 2.2 minutes. The measured rate at volume is
136 to 207 µs depending on the derivation, so the shape was right and the constant was
optimistic for balances, which were never measured separately.

The larger correction is about the instrument. A first run reported customer balances as
**slower at 10,000 documents than at 20,000**, reproducibly across best-of-three samples.
That is not a thing that can be true, and it was not noise: the fixture had only the
statistics autovacuum happened to reach in time, so the planner's choice — and every
recorded duration — depended on a race with a background daemon. With `ANALYZE` stated by
the fixture, the same derivation fell from 4,927 ms to 1,647 ms and the curve became
monotonic. The benchmark now states its statistics, and the reading that looked like a
finding about `available_credit_rows` was a finding about the fixture.

## The same arithmetic as one statement

This draft reproduces the canonical answer exactly: **3,430 documents, none missing, none
added, no amount different**, in 45 ms against 536 ms for the canonical service on the
same session. It is a draft, not the implementation — it has no effective-time cutoff yet
(FR-001 requires one) and no identity predicates (FR-004).

`account` is a role on `subledger_account` rather than a column on `ledger_entry`, which
is why the first CTE exists; reading it any other way would invent a second stored code.

```sql
WITH control_map(doc_type, account, side) AS (VALUES <one row per settleable document type, from SETTLEMENT_CONTROL>),
posting AS (
  -- `account` is a role on subledger_account, never a second stored code
  SELECT e.id, e.document_id, e.debit_credit, e.posting_group_id, e.amount,
         sa.role AS account
  FROM ledger_entry e
  JOIN subledger_account sa
    ON sa.id = e.account_id AND sa.tenant_id = e.tenant_id
  WHERE e.tenant_id = :t
),
control AS (
  SELECT DISTINCT ON (p.document_id)
         p.document_id, p.id AS control_id, p.account,
         p.debit_credit, p.posting_group_id
  FROM posting p
  JOIN document d ON d.id = p.document_id AND d.tenant_id = :t
  JOIN control_map m ON m.doc_type = d.type
                    AND m.account = p.account
                    AND m.side = p.debit_credit
  ORDER BY p.document_id, p.id
),
reversed_groups AS (
  SELECT DISTINCT original_posting_group_id AS g
  FROM ledger_reversal WHERE tenant_id = :t
),
balance AS (
  SELECT p.document_id, p.account,
         SUM(CASE p.debit_credit WHEN 'debit' THEN p.amount ELSE -p.amount END) AS signed
  FROM posting p GROUP BY p.document_id, p.account
),
live_allocation AS (
  SELECT a.amount, a.invoice_ledger_entry_id AS inv, a.payment_ledger_entry_id AS pay
  FROM settlement_allocation a
  JOIN ledger_entry pe ON pe.id = a.payment_ledger_entry_id AND pe.tenant_id = :t
  JOIN ledger_entry ie ON ie.id = a.invoice_ledger_entry_id AND ie.tenant_id = :t
  WHERE a.tenant_id = :t
    AND pe.posting_group_id NOT IN (SELECT g FROM reversed_groups)
    AND ie.posting_group_id NOT IN (SELECT g FROM reversed_groups)
),
allocated AS (
  SELECT entry_id, SUM(amount) AS amount FROM (
    SELECT inv AS entry_id, amount FROM live_allocation
    UNION ALL
    SELECT pay AS entry_id, amount FROM live_allocation
  ) x GROUP BY entry_id
)
SELECT c.document_id,
  CASE WHEN c.posting_group_id IN (SELECT g FROM reversed_groups) THEN 0
       ELSE (CASE c.debit_credit WHEN 'debit' THEN b.signed ELSE -b.signed END)
            - COALESCE(al.amount, 0)
  END AS open_amount
FROM control c
JOIN balance b ON b.document_id = c.document_id AND b.account = c.account
LEFT JOIN allocated al ON al.entry_id = c.control_id
```

### What each part answers

- `posting` resolves the account role once, so the rest of the statement can group on it.
- `control` picks the one control entry per document: the posting on the account and side
  that the document's type declares. `DISTINCT ON` takes the first, which is what the
  Python `setdefault` does over its scan.
- `reversed_groups` is every posting group some reversal names as the original.
- `balance` is `account_balance` per document and account, signed by side.
- `live_allocation` drops allocations whose payment or invoice side sits in a reversed
  group, which is what `active_settlement_allocations` does. The `UNION ALL` mirrors
  `_allocated_per_entry`, which credits an allocation to both of its entries.
- The final `CASE` is `_open_amount`: nothing open on a reversed original, otherwise the
  signed balance less what is already allocated.

## Curve of both, same companies

| finance documents | Python | SQL |
|---|---|---|
| 177 | 41 ms | 8 ms |
| 688 | 113 ms | 58 ms |
| 711 | 96 ms | 61 ms |
| 3,430 | 497 ms | 47 ms |

These four rows come from the development-database copy, not the fixture, and are kept
because they are the pair that proves the formulation. The SQL row for 3,430 documents is faster than for 688 because its cost tracks the
company's total ledger volume, not its document count — the two 700-document companies
carry more postings each. That is the point: the SQL version's cost is a fixed set of hash
aggregates over tables that indexes and partitions can bound, where the Python version's
cost is objects in one process, which they cannot.
