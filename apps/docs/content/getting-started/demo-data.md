# Demo data guide

The canonical demo company is a deterministic synthetic trading company. Use it to
see how completed and exceptional business processes look across Sales, Purchasing,
Warehouse, Finance and Analytics. The references below are searchable business labels,
not technical IDs.

Every demo business document has a document date. A dash in a due-date column means
that the source stated no due date; it never means that the document is dateless.

## Sales and fulfilment

| Reference | What to inspect | Expected result |
| --- | --- | --- |
| `O01` | Reservation | 5 pcs reserved |
| `O04` | Partial reservation | 2 pcs reserved on an overdue order |
| `O06` | Partial delivery | 3 of 5 pcs shipped; 2 remain open |
| `O07`, `O08` | Manual hold | The commitment is held and remains explainable |
| `O09` | Complete delivery | 5 of 5 pcs shipped |
| `O10` | Cancellation before shipment | Reservation history remains visible |
| `O11` | Cancellation after partial shipment | 2 pcs stay shipped; the remainder is cancelled |

The dated `H-*` orders and invoices provide comparable volume, price, decline,
outlier, zero-value and USD periods. Their invoices include open, partly paid and paid
examples.

## Customer returns and credits

| Reference | What to inspect | Expected result |
| --- | --- | --- |
| `H-credit-origin` / `CR-001` | Complete return and credit | 10 of 10 pcs returned; EUR 120 credit allocated |
| `COST-A` / `COST-LATE-CREDIT` | Partial return with costs | 10 of 60 pcs returned with exact retained cost lineage |

`COST-A` is the detailed return-and-margin example. It connects the original inventory
issue, returned inventory slice, customer credit and selling costs under one reviewed
cost boundary.

## Purchasing and payables

| Reference | Receipt | Invoice and payment | Purpose |
| --- | ---: | --- | --- |
| `PO-001` / `S01` | 2 of 5 | No invoice | Partial receipt |
| `PO-002` / `S02` | 5 of 5 | Paid | Complete purchase-to-pay |
| `PO-003` / `S03` | 0 of 5 | No invoice | Open purchase order |
| `PO-004` / `S04` | 5 of 5 | Partly paid | Partial supplier payment |
| `PO-005` / `S05` | 5 of 5 | Unpaid | Open payable |
| `PO-006` / `S06` | 5 of 5 | No invoice | Receipt awaiting invoice |
| `PO-007` / `S07` | 5 received, 2 returned | `SINV-S07`, `SCN-S07` | Supplier return with allocated credit |
| `PO-008` / `S08` | 5 received, 1 returned | `SINV-S08`, no credit | Return awaiting supplier credit |
| `PO-009` / `S09` | None | None | Purchase cancelled before receipt |

## Inventory, contribution and finance

- `P08` has stock in the other warehouse and demonstrates a location-specific shortage.
- `P16` contains a traceable movement correction.
- `COST-A` is a complete acquisition, inventory, sale, return and selling-cost story.
- The five `COST-PORTFOLIO-*` cases show healthy, low, negative, explicitly zero and
  allocation-heavy DB2 outcomes.
- Missing evidence remains **Not evidenced**. EUR 0 appears only when zero was stated or
  explicitly reviewed.
- Customer and supplier credits reduce an invoice through explicit allocations.

## Static baseline and live data

The cases above belong to the stable baseline. Live simulation separately adds customer
orders and later invoices and payments. It does not automatically reserve stock, ship,
return or replenish goods, so the reference cases remain reproducible.

The demo does not yet include price-only allowances, exchanges, post-invoice
cancellation, overdelivery, manufacturing, payroll or statutory reporting.

