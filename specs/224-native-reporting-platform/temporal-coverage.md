# Temporal Coverage Inventory

Status: first-slice design inventory; no universal historical reconstruction asserted.

| Area | Existing basis | First-slice publication | Required proof before as-of support |
|---|---|---|---|
| Sales orders/lines | Retained evidence and source versions | Business-date periods over current retained evidence | Complete version selection and late correction semantics |
| Customers/products | Current retained identity and labels | Current attributes explicitly labeled | Attribute validity history |
| Commitments | Operational Reality | Not exposed in this slice | Every relevant state transition and effective time |
| Reservations | Links to commitments | Not exposed in this slice | Release/change history and validity intervals |
| Stock | Movements | Not exposed in this slice | Opening coverage, reversals, backdating and cutoff rules |
| Invoices/open items | Evidence and canonical finance observations | Not exposed in this slice | Historical postings, reversals and settlement cutoff |
| Payment allocations | Canonical allocation relationships | Not exposed in this slice | Allocation/reversal history and knowledge-time completeness |

Database observation time, source ingestion time and business effective time are distinct.
The table lists known model foundations, not a completed code-level history audit.
T011 records exact service/table fields and counterexamples before publishing coverage.
Do not create snapshot tables to fill unknown coverage during this feature.
