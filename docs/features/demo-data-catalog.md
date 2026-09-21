# Demo Data Catalog

The canonical `international_demo` profile is a deterministic synthetic trading
company. Use it to learn how implemented processes look across Sales, Purchasing,
Warehouse, Finance and the Business Reality Inspector. Every business document has an
authored document date. A missing due date never means that the document is dateless.

This page describes profile version 4. References are human-facing labels for finding
examples, never database identity.

## Company and master data

- 16 items (`P01`–`P16`) in pcs, m and kg
- 20 customers, 3 suppliers and 2 warehouses
- EUR and USD sales evidence

## Sales and fulfillment

| Reference | Journey | Expected result |
|---|---|---|
| `O01` | Full reservation | 5 pcs reserved |
| `O04` | Overdue partial reservation | 2 pcs reserved |
| `O05` | Overdue reservation | 5 pcs reserved |
| `O06` | Partial delivery | 3 of 5 pcs shipped; 2 open |
| `O07`, `O08` | Manual hold | Commitment held with evidence intact |
| `O09` | Complete delivery | 5 of 5 pcs shipped |
| `O10` | Cancellation before shipment | Reservation history retained |
| `O11` | Cancellation after partial shipment | 2 pcs shipped; remainder cancelled |

Historical `H-*` orders have dated invoices and shipments. They cover comparable
volume, price, decline, outlier, zero-value and USD periods, with paid, partly paid and
open invoices.

## Customer returns and credits

| Reference | Journey | Expected result |
|---|---|---|
| `H-credit-origin` / `CR-001` | Full return and credit | 10 of 10 pcs returned; EUR 120 credit allocated |
| `COST-A` / `COST-LATE-CREDIT` | Partial return | 10 of 60 pcs returned with exact cost lineage |

`COST-A` is the detailed return-and-margin example. It retains the original issue cost,
returned inventory slice, customer credit and selling costs under one reviewed boundary.

## Purchasing and payables

| Reference | Receipt | Invoice/payment | Purpose |
|---|---:|---|---|
| `PO-001` / `S01` | 2 of 5 | None | Partial receipt |
| `PO-002` / `S02` | 5 of 5 | Paid | Complete purchase-to-pay |
| `PO-003` / `S03` | 0 of 5 | None | Open purchase order |
| `PO-004` / `S04` | 5 of 5 | Partly paid | Partial payment |
| `PO-005` / `S05` | 5 of 5 | Unpaid | Open payable |
| `PO-006` / `S06` | 5 of 5 | No invoice | Receipt awaiting invoice |
| `PO-007` / `S07` | 5 received, 2 returned | `SINV-S07`, `SCN-S07` | Return with allocated supplier credit |
| `PO-008` / `S08` | 5 received, 1 returned | `SINV-S08`, no credit | Return awaiting credit; intentional exception |
| `PO-009` / `S09` | None | None | Cancellation before receipt |

## Inventory, contribution and finance

- `P08` demonstrates stock at the other warehouse.
- `P16` contains a traceable movement correction.
- `COST-A` is a complete acquisition, inventory, sale, return and selling-cost story.
- Five `COST-PORTFOLIO-*` cases show healthy, low, negative, explicitly zero and
  allocation-heavy DB2 outcomes.
- Missing evidence stays labelled missing. EUR 0 appears only when zero was explicitly
  stated or reviewed.
- Customer and supplier credits reduce invoices through explicit allocations.
- Finance projections are prepared during setup; a ready demo needs no initial Refresh.

## Live demo data

Live simulation is separate from the stable baseline. It adds synthetic customer orders
and later invoices/payments, but does not automatically reserve, ship, return or
replenish goods. This keeps the reference journeys stable while the company stays active.

## Deliberate limitations

The profile does not yet model price-only allowances, exchanges/replacements,
post-invoice cancellation, overdelivery, quotations, manufacturing, serial/lot
tracking, tax advice, payroll, bank reconciliation or statutory reporting. Do not
infer an absent scenario from a similarly named document.
