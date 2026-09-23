# Demo Data Catalog

The canonical `international_demo` profile is a deterministic synthetic trading
company. Use it to learn how implemented processes look across Sales, Purchasing,
Warehouse, Finance and the Business Reality Inspector. Every business document has an
authored document date. A missing due date never means that the document is dateless.

This page describes profile version 12. References are human-facing labels for finding
examples, never database identity.

## Company and master data

- Items: Summit Bottle (`ITEM-001`), Trail Lantern (`ITEM-002`), Ridge Backpack
  (`ITEM-003`), Cedar Desk Lamp (`ITEM-004`), Coast Storage Box (`ITEM-005`),
  Harbor Travel Mug (`ITEM-006`), Aurora Notebook (`ITEM-007`), Vista Monitor
  Stand (`ITEM-008`), Maple Serving Tray (`ITEM-009`), Orbit Cable Kit
  (`ITEM-010`), Meadow Picnic Set (`ITEM-011`), Beacon Desk Organizer
  (`ITEM-012`), Drift Cushion (`ITEM-013`), Cove Glass Set (`ITEM-014`),
  Meridian Fabric (`ITEM-015`), Alpine Wax Pellets (`ITEM-016`), Willow Batch
  Balm (`ITEM-017`) and Atlas Field Scanner (`ITEM-018`).
- Customers: Northstar Outdoor, Maple Retail, Solstice Living, Pacific Outfitters,
  Brightwater Home, Juniper Trading Co., Lakeside Provisions, Fjord Outfitters,
  Harlow Interiors, Tidewater Sports, Evergreen Studio, Copperline Goods,
  Granite Peak Gear, Willow & Finch, Northbridge Office Supply, Blue Heron Living,
  Marlow Home Goods, Silverbirch Design, Cascade Trail Company and Amber Coast Retail.
- Suppliers and supplied items: Alpine Components (`ITEM-016`), Meridian Textiles
  (`ITEM-015`) and Seabright Goods (`ITEM-011`).
- Locations: Rotterdam Warehouse and Singapore Warehouse.
- Payment term: `DEMO-14-2`, 14 days net and 2 percent discount within 7 days,
  bound to every seeded customer and supplier invoice.
- EUR and USD sales evidence.

## Finding a case in the product

Search `SO-*` references under **Sales → Orders**; follow the invoice
link from the order when its `INV-*` number differs. Search `PO-*` under **Purchasing →
Orders**, `SINV-*` and `CPAY-*`/`SPAY-*` under the matching **Finance** register, and `ITEM-*` under
**Warehouse** or **Master data → Items**. Expand the line or settlement explanation to
reach the underlying Reality records and source evidence.

## Sales and fulfillment

| Reference          | Journey                             | Expected result                      |
| ------------------ | ----------------------------------- | ------------------------------------ |
| `SO-001`           | Full reservation                    | 5 pcs reserved                       |
| `SO-004`           | Overdue partial reservation         | 2 pcs reserved                       |
| `SO-005`           | Overdue reservation                 | 5 pcs reserved                       |
| `SO-006`           | Partial delivery                    | 3 of 5 pcs shipped; 2 open           |
| `SO-007`, `SO-008` | Manual hold                         | Commitment held with evidence intact |
| `SO-009`           | Complete delivery                   | 5 of 5 pcs shipped                   |
| `SO-010`           | Cancellation before shipment        | Reservation history retained         |
| `SO-011`           | Cancellation after partial shipment | 2 pcs shipped; remainder cancelled   |

Historical `SO-012`–`SO-023` orders have dated invoices and shipments. They cover comparable
volume, price, decline, outlier, zero-value and USD periods, with paid, partly paid and
open invoices.

## Customer returns and credits

| Reference           | Journey                | Expected result                                 |
| ------------------- | ---------------------- | ----------------------------------------------- |
| `SO-018` / `CN-001` | Full return and credit | 10 of 10 pcs returned; EUR 120 credit allocated |
| `SO-024` / `CN-002` | Partial return         | 10 of 60 pcs returned with exact cost lineage   |

`SO-024` is the detailed return-and-margin example. It retains the original issue cost,
returned inventory slice, customer credit and selling costs under one reviewed boundary.

## Purchasing and payables

| Reference        |                Receipt | Invoice/payment              | Purpose                                       |
| ---------------- | ---------------------: | ---------------------------- | --------------------------------------------- |
| `PO-001` / `S01` |                 2 of 5 | None                         | Partial receipt                               |
| `PO-002` / `S02` |                 5 of 5 | EUR 49 cash + EUR 1 discount | Complete discount settlement                  |
| `PO-003` / `S03` |                 0 of 5 | None                         | Open purchase order                           |
| `PO-004` / `S04` |                 5 of 5 | Partly paid                  | Partial payment                               |
| `PO-005` / `S05` |                 5 of 5 | EUR 60 paid against EUR 50   | EUR 10 supplier credit                        |
| `PO-006` / `S06` |                 5 of 5 | No invoice                   | Receipt awaiting invoice                      |
| `PO-007` / `S07` | 5 received, 2 returned | `SINV-007`, `SCN-007`        | Return with allocated supplier credit         |
| `PO-008` / `S08` | 5 received, 1 returned | `SINV-008`, no credit        | Return awaiting credit; intentional exception |
| `PO-009` / `S09` |                   None | None                         | Cancellation before receipt                   |

## Inventory, contribution and finance

- `ITEM-008` demonstrates stock at the other warehouse (`wrong-location`).
- `ITEM-016` contains the retained `correction-original` and its
  `correction-replacement`.
- `SO-024` is a complete acquisition, inventory, sale, return and selling-cost story.
- Five `COST-PORTFOLIO-*` cases show healthy, low, negative, explicitly zero and
  allocation-heavy DB2 outcomes.
- Missing evidence stays labelled missing. EUR 0 appears only when zero was explicitly
  stated or reviewed.
- Customer and supplier credits reduce invoices through explicit allocations.
- Finance projections are prepared during setup; a ready demo needs no initial Refresh.
- `SO-030` plus `CN-003` is a price-only allowance without a return movement.
- `SO-031` has an invoice whose posting group is preserved beside its exact inverse.
- `SO-032` has two partial invoices for quantities 4 and 6 on one order line.
- `SO-011` is the final underdelivery: 2 pcs shipped and the remainder cancelled.
- `ITEM-017` / `LOT-2026-001` shows an expired lot and a 3-pcs warehouse transfer.
- `ITEM-018` / `SER-0001` shows serial-controlled receipt.
- `ITEM-010` has separate source-backed damage, loss and scrap adjustments.
- `SO-033` is shipped and returned; `SO-034` is its separately stated zero-price
  replacement shipment.
- `SO-035` is invoiced and paid through `CPAY-010` before its later shipment.
- `DN-2026-0001` is a level-2 reminder with a separately posted EUR 5 fee.
- `SO-037` retains EUR 15 after EUR 60 cash and a confirmed EUR 25 bad-debt adjustment.
- `CDEP-001` clears EUR 80 into the final invoice behind `SO-038` and leaves EUR 20 credit.
- `SDEP-001` clears EUR 100 into `SINV-010` and leaves EUR 20 supplier credit.
- `SO-039` preserves its original 10-pcs promise, its revision to 12 and the later 12-pcs shipment.

## Deterministic settlement questions

| Question                 | Reference and UI path                                          | Expected result                                                                            |
| ------------------------ | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Supplier discount        | Finance → Payables → `SINV-002`; payment `SPAY-002`            | EUR 49 cash plus a separate EUR 1 accepted discount; invoice open EUR 0                    |
| Customer overpayment     | Sales → `SO-020` → invoice; or Finance → Payments → `CPAY-009` | EUR 5,000 allocated; EUR 10 available customer credit                                      |
| Supplier overpayment     | Finance → Payables → `SINV-005`; or Payments → `SPAY-005`      | EUR 50 allocated; EUR 10 available supplier credit                                         |
| Accepted small remainder | Sales → `SO-017` → invoice; payment `CPAY-006`                 | EUR 74.50 cash plus a separately evidenced EUR 0.50 accepted remainder; invoice open EUR 0 |

The payment remains evidence of cash only. Accepted reductions are separate postings,
and overpayment credit remains unallocated until a later reviewed allocation or refund.

## Live demo data

Live simulation is separate from the stable baseline. It adds synthetic customer orders
and later invoices/payments, but does not automatically reserve, ship, return or
replenish goods. This keeps the reference journeys stable while the company stays active.

Each scheduled delivery produces zero to six orders. Invoices follow after 2–10 minutes
and use `DEMO-14-2`. The deterministic long-run settlement mix is 91% exact, 2% stated
discount, 1% freight withheld, 1% two-part payment, 1% overpayment/duplicate, 1%
unmatched, 2% late and 1% never paid. It is a probability distribution, not guaranteed
coverage within a small sample. Provider and bank paths are retained as separate source
evidence.

## Exceptional source evidence

- `shipment-cancelled-remainder` is the shipment retained for `SO-011`.
- `COST-LATE-CLEANUP` is the 10-unit `ITEM-003` outbound cleanup preceding the
  reviewed `SO-024` layer.
- `history-receipt-*` and `history-shipment-*` back `SO-012`–`SO-023`.
- `purchase-receipt-S01`, `S02`, `S04`–`S08` back the received purchase cases.
  There is intentionally no `purchase-receipt-S03`, because `PO-003` has no receipt.
- `COST-A-SELLING` states EUR 114 selling cost for `SO-024`;
  `COST-PORTFOLIO-SELLING` states the portfolio allocation for `SO-025`–`SO-029`.

## Demo modes

- **International demo:** create a Sandbox Demo company in the company UI.
- **International demo plus live data:** enable Live simulation in that same creation
  flow; the fixed baseline remains unchanged.
- **`atlas-execution`:** deliberately reduced two-item, two-order, one-location fixture
  for guided execution lessons, not the canonical sales-demo data set.
- **`normal-month`:** CLI-only September 2026 service scenario, started with
  `reality scenario run normal-month --tenant TENANT_ID`.

## Deliberate limitations

The profile does not model automatic dunning runs/delivery, jurisdiction-specific tax
treatment, quotations, manufacturing, tax/FX revaluation, payroll, bank reconciliation
or statutory reporting. Manual dunning, explicit deposit clearing, confirmed bad debt
and commitment-amended overdelivery are present as normal product workflows.
