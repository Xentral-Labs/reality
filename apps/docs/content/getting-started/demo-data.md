# Demo data guide

The canonical demo company is a deterministic synthetic trading company. Use it to
see how completed and exceptional business processes look across Sales, Purchasing,
Warehouse, Finance and Analytics. The references below are searchable business labels,
not technical IDs.

Every demo business document has a document date. A dash in a due-date column means
that the source stated no due date; it never means that the document is dateless.

## Company and how to use the references

The baseline contains 16 items (`P01`–`P16`), 20 customers, three suppliers and the
Rotterdam and Singapore warehouses. Quantities use pieces, metres or kilograms. Most
trades use EUR; two invoices deliberately use USD to keep currencies separate.

Search for a reference, then open its order, invoice, movement or Finance entry. From
an important value you can follow the Reality record to document evidence and the
original synthetic source payload. The same profile version creates the same cases in
every fresh company.

## Sales and fulfilment

| Reference | What to inspect | Expected result |
| --- | --- | --- |
| `O01` | Reservation | 5 pcs reserved |
| `O02` | Stock without reservation | 5 ordered, 10 in stock, nothing reserved |
| `O03` | Stock shortage | 5 ordered but only 2 available |
| `O04` | Partial reservation | 2 pcs reserved on an overdue order |
| `O06` | Partial delivery | 3 of 5 pcs shipped; 2 remain open |
| `O07`, `O08` | Manual hold | The commitment is held and remains explainable |
| `O09` | Complete delivery | 5 of 5 pcs shipped |
| `O10` | Cancellation before shipment | Reservation history remains visible |
| `O11` | Cancellation after partial shipment | 2 pcs stay shipped; the remainder is cancelled |

The dated `H-*` orders and invoices provide comparable volume, price, decline,
outlier, zero-value and USD periods. Their invoices include open, partly paid and paid
examples.

Orders are evidence, not fulfilment state. A delivery promise is a Commitment,
reservations are separate records, and only Movements change physical stock. Cancelling
`O10` or `O11` therefore never erases a reservation or shipment that already happened.

## Historical sales and invoices

| Reference | Stated trade | Settlement | Purpose |
| --- | --- | --- | --- |
| `H-volume-prior` | 10 × `P11`, EUR 200 | Paid | Earlier quantity baseline |
| `H-volume-current` | 20 × `P11`, EUR 400 | Paid | Current volume comparison |
| `H-price-prior` | 10 × `P12`, EUR 200 | Paid | Earlier price baseline |
| `H-price-current` | 10 × `P12`, EUR 250 | Partly paid | Same quantity, higher price |
| `H-decline-prior` | 20 × `P13`, EUR 300 | Paid | Earlier demand baseline |
| `H-decline-current` | 5 × `P13`, EUR 75 | Open | Visible sales decline |
| `H-credit-origin` | 10 × `P14`, EUR 120 | Settled by credit | Complete return origin |
| `H-outlier-prior` | 10 × `P15`, EUR 50 | Paid | Ordinary comparison value |
| `H-outlier-current` | 1,000 × `P15`, EUR 5,000 | Open | Deliberate outlier |
| `H-zero-current` | 8 × `P16`, EUR 80 | Open | Authored comparison, not missing money |
| `H-usd-prior` | 4 × `P09`, USD 88 | Paid | Earlier foreign-currency evidence |
| `H-usd-current` | 6 × `P09`, USD 132 | Paid | Current foreign-currency evidence |

Each case has an order, customer delivery Commitment, dated invoice, opening-stock
Movement and shipment Movement. Payments are separate documents and ledger postings:
paid does not mean delivered, and delivered does not mean paid.

## Customer returns and credits

| Reference | What to inspect | Expected result |
| --- | --- | --- |
| `H-credit-origin` / `CR-001` | Complete return and credit | 10 of 10 pcs returned; EUR 120 credit allocated |
| `COST-A` / `COST-LATE-CREDIT` | Partial return with costs | 10 of 60 pcs returned with exact retained cost lineage |

`COST-A` is the detailed return-and-margin example. It connects the original inventory
issue, returned inventory slice, customer credit and selling costs under one reviewed
cost boundary.

`CR-001` is explicitly allocated to its invoice, leaving no receivable. The partial
`COST-LATE-CREDIT` retains the exact cost slice of the ten returned units instead of
inventing a new acquisition value.

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

A supplier Commitment records what is expected, a receipt records what arrived, an
invoice creates the payable, and a payment settles it. `S06` proves why received and
invoiced are different states. `S08` intentionally remains unresolved so “returned to
supplier and not credited” has real evidence to explain.

## Documents in the baseline

| Document | Examples | Meaning |
| --- | --- | --- |
| Sales order | `O01`–`O11`, `H-*`, `COST-*` | Stated customer demand and commercial lines |
| Purchase order | `PO-001`–`PO-009` | Order placed with a supplier |
| Sales invoice | `INV-YYYYMMDD-*` | Customer receivable backed by invoice lines |
| Supplier invoice | `SINV-S02`, `SINV-S04`, `SINV-S05`, `SINV-S07`, `SINV-S08` | Payable independent of receipt state |
| Customer credit note | `CR-001`, `COST-LATE-CREDIT` | Full and partial customer value reversal |
| Supplier credit note | `SCN-S07` | Supplier value reversal allocated to its invoice |
| Customer payment | `PAY-*` | Full or partial receivable settlement |
| Supplier payment | `SPAY-S02`, `SPAY-S04` | Full or partial payable settlement |

All carry a document date. Their readable numbers help search; opaque tenant-scoped IDs
remain the actual identity.

## Physical movements in the baseline

| Movement | Examples | Physical effect |
| --- | --- | --- |
| Opening stock | `opening-P01`, history and cost openings | Adds a stated starting quantity |
| Receipt | `purchase-receipt-S01`–`S08` | Adds goods received from a supplier |
| Shipment | `shipment-P06`, `shipment-P09`, `H-*`, `COST-*` | Removes goods sent to a customer |
| Customer return | `return-001`, `COST-LATE-RETURN` | Adds previously shipped goods back |
| Supplier return | `supplier-return-S07`, `supplier-return-S08` | Removes goods sent back to a supplier |
| Correction | `P16` correction pair | Keeps the original and records its correction |

Stock is the signed result of these movements per location. No invoice or document
status owns the physical quantity.

## Inventory, contribution and finance

- `P08` has stock in the other warehouse and demonstrates a location-specific shortage.
- `P16` contains a traceable movement correction.
- `COST-A` is a complete acquisition, inventory, sale, return and selling-cost story.
- The five `COST-PORTFOLIO-*` cases show healthy, low, negative, explicitly zero and
  allocation-heavy DB2 outcomes.
- Missing evidence remains **Not evidenced**. EUR 0 appears only when zero was stated or
  explicitly reviewed.
- Customer and supplier credits reduce an invoice through explicit allocations.

### Exact DB1 and DB2 examples

| Case | Revenue | Goods cost | DB1 | Selling costs | DB2 | Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `COST-A` | EUR 1,200 | EUR 630 | EUR 570 | EUR 114 | EUR 456 | 38% |
| `COST-PORTFOLIO-HEALTHY` | EUR 250 | EUR 100 | EUR 150 | EUR 25 | EUR 125 | 50% |
| `COST-PORTFOLIO-LOW` | EUR 150 | EUR 100 | EUR 50 | EUR 40 | EUR 10 | 6.6667% |
| `COST-PORTFOLIO-NEGATIVE` | EUR 130 | EUR 100 | EUR 30 | EUR 60 | EUR −30 | −23.0769% |
| `COST-PORTFOLIO-ZERO-SELLING` | EUR 180 | EUR 100 | EUR 80 | EUR 0 | EUR 80 | 44.4444% |
| `COST-PORTFOLIO-ALLOCATED-HEAVY` | EUR 220 | EUR 100 | EUR 120 | EUR 60 | EUR 60 | 27.2727% |

The zero-selling case is an explicitly reviewed zero, not missing evidence. Every
seeded sales invoice line has a reviewed contribution basis. **Not evidenced** means
Reality refused to turn missing evidence into EUR 0.

## Coverage and deliberate gaps

| Typical process | Included | Evidence or limitation |
| --- | --- | --- |
| Open order, shortage and reservation | Yes | `O01`–`O05` |
| Partial/complete delivery and manual hold | Yes | `O06`–`O09` |
| Cancellation before/after shipment | Yes | `O10`, `O11` |
| Open, partial and paid receivable | Yes | `H-*`, `PAY-*` |
| Complete and partial customer return/credit | Yes | `CR-001`, `COST-LATE-CREDIT` |
| No, partial and complete supplier receipt | Yes | `S01`–`S03` |
| Receipt without invoice | Yes | `S06` |
| Open, partial and paid payable | Yes | `S05`, `S04`, `S02` |
| Supplier return with/without credit | Yes | `S07`, `S08` |
| Purchase cancellation before receipt | Yes | `S09` |
| Location shortage and correction | Yes | `P08`, `P16` |
| Complete DB1/DB2 explanations | Yes | `COST-A`, `COST-PORTFOLIO-*` |
| Price-only allowance | No | Not in profile version 4 |
| Exchange or replacement delivery | No | Not in profile version 4 |
| Invoice cancellation/reversal | No | Not in profile version 4 |
| Multiple partial invoices per order | No | Not in profile version 4 |
| Overdelivery/final short-delivery closure | No | Not in profile version 4 |
| Warehouse transfer, damage, loss or scrap | No | Not in profile version 4 |
| Lots, serial numbers or expiry dates | No | Not in profile version 4 |
| Deposits, dunning or bad debt | No | Not in profile version 4 |
| Bank reconciliation, tax or FX revaluation | No | Not in profile version 4 |

## Static baseline and live data

The cases above belong to the stable baseline. Live simulation separately adds customer
orders and later invoices and payments. It does not automatically reserve stock, ship,
return or replenish goods, so the reference cases remain reproducible.

The demo does not yet include price-only allowances, exchanges, post-invoice
cancellation, overdelivery, manufacturing, payroll or statutory reporting.
