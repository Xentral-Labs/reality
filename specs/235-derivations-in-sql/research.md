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

## The cost is linear in the company

| finance documents | `financial_open_items` | per document |
|---|---|---|
| 24 | 6 ms | 260 µs |
| 177 | 25 ms | 142 µs |
| 688 | 84 ms | 122 µs |
| 711 | 84 ms | 119 µs |
| 3,430 | 454 ms | 132 µs |

The first row is startup noise. From 177 documents upwards the cost per document is flat,
so the total is linear: 2.6 s at the current 20,000 cap, 13 s at 100,000, 2.2 minutes at
a million, 22 minutes at ten million.

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

The SQL row for 3,430 documents is faster than for 688 because its cost tracks the
company's total ledger volume, not its document count — the two 700-document companies
carry more postings each. That is the point: the SQL version's cost is a fixed set of hash
aggregates over tables that indexes and partitions can bound, where the Python version's
cost is objects in one process, which they cannot.
