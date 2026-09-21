---
pageClass: demo-data-page
---

# Demo data guide

The canonical demo company is a deterministic synthetic trading company. Use it to see how completed
and exceptional business processes look across Sales, Purchasing, Warehouse, Finance and Analytics.
The references below are searchable business labels, not technical IDs.

Every demo business document has a document date. A dash in a due-date column means that the source
stated no due date; it never means that the document is dateless.

## Company and how to use the references

The baseline contains 18 items (`ITEM-001`–`ITEM-018`), 20 customers, three suppliers and the
Rotterdam and Singapore warehouses. Quantities use pieces, metres or kilograms. Most trades use EUR;
two invoices deliberately use USD to keep currencies separate.

<details class="demo-data-inventory">
<summary><strong>Complete master-data inventory</strong> — 18 items, 20 customers, 3 suppliers, 2 warehouses and the shared payment term</summary>

### Master-data inventory

| Type         | Included records                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Where they appear                                                                        |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Items        | `ITEM-001` Summit Bottle; `ITEM-002` Trail Lantern; `ITEM-003` Ridge Backpack; `ITEM-004` Cedar Desk Lamp; `ITEM-005` Coast Storage Box; `ITEM-006` Harbor Travel Mug; `ITEM-007` Aurora Notebook; `ITEM-008` Vista Monitor Stand; `ITEM-009` Maple Serving Tray; `ITEM-010` Orbit Cable Kit; `ITEM-011` Meadow Picnic Set; `ITEM-012` Beacon Desk Organizer; `ITEM-013` Drift Cushion; `ITEM-014` Cove Glass Set; `ITEM-015` Meridian Fabric; `ITEM-016` Alpine Wax Pellets; `ITEM-017` Willow Batch Balm; `ITEM-018` Atlas Field Scanner | Master data → Items; Warehouse → Items                                                   |
| Customers    | Northstar Outdoor; Maple Retail; Solstice Living; Pacific Outfitters; Brightwater Home; Juniper Trading Co.; Lakeside Provisions; Fjord Outfitters; Harlow Interiors; Tidewater Sports; Evergreen Studio; Copperline Goods; Granite Peak Gear; Willow & Finch; Northbridge Office Supply; Blue Heron Living; Marlow Home Goods; Silverbirch Design; Cascade Trail Company; Amber Coast Retail                                                                                                                                              | Master data → Business partners; customer names also appear on sales orders and invoices |
| Suppliers    | Alpine Components (`ITEM-016`); Meridian Textiles (`ITEM-015`); Seabright Goods (`ITEM-011`)                                                                                                                                                                                                                                                                                                                                                                                                                                               | Master data → Business partners; Purchasing → Orders                                     |
| Warehouses   | Rotterdam Warehouse; Singapore Warehouse                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Warehouse → Items → expand stock by location                                             |
| Payment term | `DEMO-14-2`: 14 days net, 2% discount within 7 days                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Open any seeded customer or supplier invoice and inspect its payment term                |

Northstar Outdoor, Maple Retail, Solstice Living and Blue Heron Living occur repeatedly in the dated
sales series; the other customers provide authored one-off comparisons. Supplier-to-item
relationships are stated above rather than inferred from a receipt.

</details>

Search each reference in its matching view:

- **Sales → Orders:** search for `SO-001`, `SO-011`, `SO-017` or `SO-024`.
- **Purchasing → Orders:** search for `PO-001` through `PO-009`.
- **Finance → Receivables/Payables:** search for an `INV-*`/`SINV-*` number, party or one of the
  exact `CPAY-*`/`SPAY-*` references below.
- **Warehouse:** open an item such as `ITEM-008` or `ITEM-016`, then expand stock and movements.
- **Analytics/Contribution:** search for `SO-024` or `SO-025`, then open the explanation below the
  invoice line.

When an invoice number differs from its order number, start at the order and follow its invoice
link. From an important value you can continue through the Reality record, document evidence and
original synthetic source payload.

## Sales and fulfilment

| Reference          | What to inspect                     | Expected result                                | How to find it                                     |
| ------------------ | ----------------------------------- | ---------------------------------------------- | -------------------------------------------------- |
| `SO-001`           | Reservation                         | 5 pcs reserved                                 | Sales → Orders → search `SO-001` → expand the line |
| `SO-002`           | Stock without reservation           | 5 ordered, 10 in stock, nothing reserved       | Sales → Orders → `SO-002`                          |
| `SO-003`           | Stock shortage                      | 5 ordered but only 2 available                 | Sales → Orders → `SO-003` → availability           |
| `SO-004`           | Partial reservation                 | 2 pcs reserved on an overdue order             | Sales → Orders → `SO-004` → reservations           |
| `SO-005`           | Overdue full reservation            | 5 pcs reserved; the promise is overdue         | Sales → Orders → `SO-005` → reservations/history   |
| `SO-006`           | Partial delivery                    | 3 of 5 pcs shipped; 2 remain open              | Sales → Orders → `SO-006` → deliveries             |
| `SO-007`, `SO-008` | Manual hold                         | The commitment is held and remains explainable | Sales → Orders → reference → commitment            |
| `SO-009`           | Complete delivery                   | 5 of 5 pcs shipped                             | Sales → Orders → `SO-009` → deliveries             |
| `SO-010`           | Cancellation before shipment        | Reservation history remains visible            | Sales → Orders → `SO-010` → history                |
| `SO-011`           | Cancellation after partial shipment | 2 pcs stay shipped; the remainder is cancelled | Sales → Orders → `SO-011` → deliveries/history     |

The dated orders `SO-012` through `SO-023` and their invoices provide comparable volume, price,
decline, outlier, zero-value and USD periods. Their invoices include open, partly paid and paid
examples.

Orders are evidence, not fulfilment state. A delivery promise is a Commitment, reservations are
separate records, and only Movements change physical stock. Cancelling `SO-010` or `SO-011`
therefore never erases a reservation or shipment that already happened.

## Historical sales and invoices

| Reference | Stated trade                  | Settlement                                  | Purpose                                | How to find it                                 |
| --------- | ----------------------------- | ------------------------------------------- | -------------------------------------- | ---------------------------------------------- |
| `SO-012`  | 10 × `ITEM-011`, EUR 200      | Paid                                        | Earlier quantity baseline              | Sales → Orders → `SO-012`                      |
| `SO-013`  | 20 × `ITEM-011`, EUR 400      | Paid                                        | Current volume comparison              | Sales → Orders → `SO-013`                      |
| `SO-014`  | 10 × `ITEM-012`, EUR 200      | Paid                                        | Earlier price baseline                 | Sales → Orders → `SO-014`                      |
| `SO-015`  | 10 × `ITEM-012`, EUR 250      | Partly paid                                 | Same quantity, higher price            | Sales → Orders → `SO-015`                      |
| `SO-016`  | 20 × `ITEM-013`, EUR 300      | Paid                                        | Earlier demand baseline                | Sales → Orders → `SO-016`                      |
| `SO-017`  | 5 × `ITEM-013`, EUR 75        | EUR 74.50 paid; EUR 0.50 accepted remainder | Sales decline and explicit closure     | Sales → Orders → `SO-017`; open invoice        |
| `SO-018`  | 10 × `ITEM-014`, EUR 120      | Settled by credit                           | Complete return origin                 | Sales → Orders → `SO-018`; open invoice/credit |
| `SO-019`  | 10 × `ITEM-015`, EUR 50       | Paid                                        | Ordinary comparison value              | Sales → Orders → `SO-019`                      |
| `SO-020`  | 1,000 × `ITEM-015`, EUR 5,000 | Paid; EUR 10 customer credit                | Deliberate outlier plus overpayment    | Sales → Orders → `SO-020`; open invoice        |
| `SO-021`  | 8 × `ITEM-016`, EUR 80        | Open                                        | Authored comparison, not missing money | Sales → Orders → `SO-021`                      |
| `SO-022`  | 4 × `ITEM-009`, USD 88        | Paid                                        | Earlier foreign-currency evidence      | Sales → Orders → `SO-022`                      |
| `SO-023`  | 6 × `ITEM-009`, USD 132       | Paid                                        | Current foreign-currency evidence      | Sales → Orders → `SO-023`                      |

Each case has an order, customer delivery Commitment, dated invoice, opening-stock Movement and
shipment Movement. Payments are separate documents and ledger postings: paid does not mean
delivered, and delivered does not mean paid.

## Customer returns and credits

| Reference           | What to inspect            | Expected result                                        | How to find it                                                |
| ------------------- | -------------------------- | ------------------------------------------------------ | ------------------------------------------------------------- |
| `SO-018` / `CN-001` | Complete return and credit | 10 of 10 pcs returned; EUR 120 credit allocated        | Sales → Orders → `SO-018`; open invoice and credit            |
| `SO-024` / `CN-002` | Partial return with costs  | 10 of 60 pcs returned with exact retained cost lineage | Sales → Orders → `SO-024`; invoice → contribution explanation |

`SO-024` is the detailed return-and-margin example. It connects the original inventory issue,
returned inventory slice, customer credit and selling costs under one reviewed cost boundary.

`CN-001` is explicitly allocated to its invoice, leaving no receivable. The partial `CN-002` retains
the exact cost slice of the ten returned units instead of inventing a new acquisition value.

## Purchasing and payables

| Reference |                Receipt | Invoice and payment                             | Purpose                               | How to find it                                         |
| --------- | ---------------------: | ----------------------------------------------- | ------------------------------------- | ------------------------------------------------------ |
| `PO-001`  |                 2 of 5 | No invoice                                      | Partial receipt                       | Purchasing → Orders → `PO-001`                         |
| `PO-002`  |                 5 of 5 | `SINV-002`, `SPAY-002`: EUR 49 + EUR 1 discount | Complete discount settlement          | Purchasing → `PO-002`; Finance → Payables → `SINV-002` |
| `PO-003`  |                 0 of 5 | No invoice                                      | Open purchase order                   | Purchasing → Orders → `PO-003`                         |
| `PO-004`  |                 5 of 5 | `SINV-004`, `SPAY-004`: partly paid             | Partial supplier payment              | Finance → Payables → `SINV-004`                        |
| `PO-005`  |                 5 of 5 | `SINV-005`, `SPAY-005`: EUR 60 against EUR 50   | EUR 10 supplier credit                | Finance → Payables → `SINV-005`                        |
| `PO-006`  |                 5 of 5 | No invoice                                      | Receipt awaiting invoice              | Purchasing → Orders → `PO-006`                         |
| `PO-007`  | 5 received, 2 returned | `SINV-007`, `SCN-007`                           | Supplier return with allocated credit | Purchasing → `PO-007`; Finance → `SINV-007`            |
| `PO-008`  | 5 received, 1 returned | `SINV-008`, no credit                           | Return awaiting supplier credit       | Purchasing → `PO-008`; Finance → `SINV-008`            |
| `PO-009`  |                   None | None                                            | Purchase cancelled before receipt     | Purchasing → Orders → `PO-009`                         |

A supplier Commitment records what is expected, a receipt records what arrived, an invoice creates
the payable, and a payment settles it. `PO-006` proves why received and invoiced are different
states. `PO-008` intentionally remains unresolved so “returned to supplier and not credited” has
real evidence to explain.

## Discounts, overpayments and accepted small remainders

| Sales-demo question                          | Guaranteed case             | How to find it                                                          | Expected result                                                                         |
| -------------------------------------------- | --------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Was the discount actually posted?            | `SINV-002` / `SPAY-002`     | Finance → Payables → `SINV-002`; open payment/allocation details        | EUR 49 cash plus a separately evidenced EUR 1 discount adjustment; open EUR 0           |
| What happens when a customer overpays?       | Order `SO-020` / `CPAY-009` | Sales → Orders → `SO-020` → invoice; or Finance → Payments → `CPAY-009` | EUR 5,000 allocated and EUR 10 available customer credit                                |
| What happens when we overpay a supplier?     | `SINV-005` / `SPAY-005`     | Finance → Payables → `SINV-005`; open payment/allocation details        | EUR 50 allocated and EUR 10 available supplier credit                                   |
| Can an old immaterial remainder be accepted? | Order `SO-017` / `CPAY-006` | Sales → Orders → `SO-017` → invoice → settlement explanation            | EUR 74.50 cash plus a separate EUR 0.50 accepted-small-remainder adjustment; open EUR 0 |

A payment difference is never silently reinterpreted. The payment states only the cash that moved.
Discount and accepted remainder are separate reasoned postings; an overpayment remains available
credit for later allocation or refund.

## Documents in the baseline

| Document             | Examples                                                                           | Meaning                                          | How to find it                         |
| -------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------ | -------------------------------------- |
| Sales order          | `SO-001`–`SO-035`                                                                  | Stated customer demand and commercial lines      | Sales → Orders → search `SO-…`         |
| Purchase order       | `PO-001`–`PO-009`                                                                  | Order placed with a supplier                     | Purchasing → Orders → search `PO-…`    |
| Sales invoice        | `INV-YYYYMMDD-*`                                                                   | Customer receivable backed by invoice lines      | Finance → Receivables → search `INV-…` |
| Supplier invoice     | `SINV-002`, `SINV-004`, `SINV-005`, `SINV-007`, `SINV-008`, `SINV-010`, `SINV-011` | Payable independent of receipt state             | Finance → Payables → search `SINV-…`   |
| Customer credit note | `CN-001`, `CN-002`                                                                 | Full and partial customer value reversal         | Finance → Receivables → search `CN-…`  |
| Supplier credit note | `SCN-007`                                                                          | Supplier value reversal allocated to its invoice | Finance → Payables → search `SCN-007`  |
| Customer payment     | `CPAY-001` onward                                                                  | Full or partial receivable settlement            | Finance → Payments → search `CPAY-…`   |
| Supplier payment     | `SPAY-002`, `SPAY-004`, `SPAY-005`                                                 | Discount, partial and overpayment examples       | Finance → Payments → search `SPAY-…`   |

All carry a document date. Their readable numbers help search; opaque tenant-scoped IDs remain the
actual identity.

## Physical movements in the baseline

| Movement        | Examples                                     | Physical effect                               | How to find it                                             |
| --------------- | -------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------- |
| Opening stock   | Item stock                                   | Adds a stated starting quantity               | Warehouse → Items → e.g. `ITEM-001` → movements            |
| Receipt         | For `PO-001`–`PO-008`                        | Adds goods received from a supplier           | Purchasing → order → receipt; or Warehouse → item          |
| Shipment        | For `SO-006`, `SO-009` and historical orders | Removes goods sent to a customer              | Sales → order → deliveries                                 |
| Customer return | For `SO-018`, `SO-024`                       | Adds previously shipped goods back            | Sales → order → invoice/credit; Warehouse → item movements |
| Supplier return | For `PO-007`, `PO-008`                       | Removes goods sent back to a supplier         | Purchasing → order → movements                             |
| Correction      | On `ITEM-016`                                | Keeps the original and records its correction | Warehouse → Items → `ITEM-016` → movements                 |

Stock is the signed result of these movements per location. No invoice or document status owns the
physical quantity.

## Inventory, contribution and finance

- `ITEM-008` has stock in the other warehouse and demonstrates a location-specific shortage.
- `ITEM-016` contains a traceable movement correction.
- `SO-024` is a complete acquisition, inventory, sale, return and selling-cost story.
- Orders `SO-025` through `SO-029` show healthy, low, negative, explicitly zero and allocation-heavy
  DB2 outcomes.
- Missing evidence remains **Not evidenced**. EUR 0 appears only when zero was stated or explicitly
  reviewed.
- Customer and supplier credits reduce an invoice through explicit allocations.

### Exact DB1 and DB2 examples

| Case     |   Revenue | Goods cost |     DB1 | Selling costs |     DB2 |      Rate | How to find it                                                 |
| -------- | --------: | ---------: | ------: | ------------: | ------: | --------: | -------------------------------------------------------------- |
| `SO-024` | EUR 1,200 |    EUR 630 | EUR 570 |       EUR 114 | EUR 456 |       38% | Sales → Orders → `SO-024` → invoice → contribution explanation |
| `SO-025` |   EUR 250 |    EUR 100 | EUR 150 |        EUR 25 | EUR 125 |       50% | Sales → Orders → `SO-025` → invoice → contribution explanation |
| `SO-026` |   EUR 150 |    EUR 100 |  EUR 50 |        EUR 40 |  EUR 10 |   6.6667% | Sales → Orders → `SO-026` → invoice → contribution explanation |
| `SO-027` |   EUR 130 |    EUR 100 |  EUR 30 |        EUR 60 | EUR −30 | −23.0769% | Sales → Orders → `SO-027` → invoice → contribution explanation |
| `SO-028` |   EUR 180 |    EUR 100 |  EUR 80 |         EUR 0 |  EUR 80 |  44.4444% | Sales → Orders → `SO-028` → invoice → contribution explanation |
| `SO-029` |   EUR 220 |    EUR 100 | EUR 120 |        EUR 60 |  EUR 60 |  27.2727% | Sales → Orders → `SO-029` → invoice → contribution explanation |

The zero-selling case is an explicitly reviewed zero, not missing evidence. Every seeded sales
invoice line has a reviewed contribution basis. **Not evidenced** means Reality refused to turn
missing evidence into EUR 0.

## Coverage and deliberate gaps

| Typical process                             | Evidence or limitation                            | How to find it                                                          |
| ------------------------------------------- | ------------------------------------------------- | ----------------------------------------------------------------------- |
| Open order, shortage and reservation        | `SO-001`–`SO-005`                                 | Sales → Orders → search reference                                       |
| Partial/complete delivery and manual hold   | `SO-006`–`SO-009`                                 | Sales → Orders → search reference                                       |
| Cancellation before/after shipment          | `SO-010`, `SO-011`                                | Sales → Orders → reference → history                                    |
| Open, partial and paid receivable           | `SO-012`–`SO-023`, `CPAY-*`                       | Sales → order → invoice; Finance → Receivables                          |
| Discount with separate reduction posting    | `SINV-002`, `SPAY-002`                            | Finance → Payables → `SINV-002`                                         |
| Customer and supplier overpayment credit    | `CPAY-009`, `SPAY-005`                            | Finance → Payments → search reference                                   |
| Accepted small remainder                    | `CPAY-006`                                        | Sales → `SO-017` → invoice → settlement                                 |
| Complete and partial customer return/credit | `CN-001`, `CN-002`                                | Finance → Receivables → search credit number                            |
| No, partial and complete supplier receipt   | `PO-001`–`PO-003`                                 | Purchasing → Orders → search reference                                  |
| Receipt without invoice                     | `PO-006`                                          | Purchasing → Orders → `PO-006`                                          |
| Open, partial and paid payable              | `SINV-005`, `SINV-004`, `SINV-002`                | Finance → Payables → search reference                                   |
| Supplier return with/without credit         | `PO-007`, `PO-008`                                | Purchasing → Orders → open reference                                    |
| Purchase cancellation before receipt        | `PO-009`                                          | Purchasing → Orders → `PO-009`                                          |
| Location shortage and correction            | `ITEM-008`, `ITEM-016`                            | Warehouse → Items → search reference                                    |
| Complete DB1/DB2 explanations               | `SO-024`–`SO-029`                                 | Sales → order → invoice → contribution explanation                      |
| Price-only allowance                        | `SO-030`, `CN-003`                                | Sales → Orders → `SO-030`; Finance → search `CN-003`                    |
| Exchange or replacement delivery            | `SO-033` return, `SO-034` replacement             | Sales → Orders → open both references; Warehouse → `ITEM-007` movements |
| Invoice cancellation/reversal               | `SO-031`, exact inverse posting                   | Sales → Orders → `SO-031` → invoice → ledger explanation                |
| Multiple partial invoices per order         | `SO-032`, quantities 4 and 6                      | Sales → Orders → `SO-032` → invoices                                    |
| Final short-delivery closure                | `SO-011`: 2 shipped, remainder cancelled          | Sales → Orders → `SO-011` → history                                     |
| Customer prepayment before shipment         | `SO-035`, `CPAY-010`                              | Sales → Orders → `SO-035` → invoice; Finance → payment                  |
| Controlled overdelivery                     | `SO-039`: quantity 10 revised to 12, then shipped | Sales → Orders → `SO-039` → commitment history                          |
| Warehouse transfer                          | `ITEM-017`, 3 pcs Rotterdam → Singapore           | Warehouse → Items → `ITEM-017` → movements                              |
| Damage, loss and scrap                      | `ITEM-010`, one adjustment each                   | Warehouse → Items → `ITEM-010` → movements                              |
| Lot and expiry date                         | `ITEM-017`, `LOT-2026-001` expired                | Warehouse → Items → `ITEM-017` → lots/movements                         |
| Serial number                               | `ITEM-018`, `SER-0001`                            | Warehouse → Items → `ITEM-018` → serial/movements                       |
| Customer deposit and final invoice          | `CDEP-001`, `SO-038`; EUR 20 credit remains       | Finance → Customer credits → `CDEP-001`; Sales → `SO-038`               |
| Supplier deposit and final invoice          | `SDEP-001`, `SINV-010`; EUR 20 credit remains     | Finance → Supplier credits → `SDEP-001`; Payables → `SINV-010`          |
| Dunning with a stated fee                   | `DN-2026-0001`; level 2 plus EUR 5 fee            | Finance → Receivables → search notice/invoice and open its explanation  |
| Partial bad-debt write-off                  | `SO-037`; EUR 25 written off, EUR 15 remains      | Sales → Orders → `SO-037` → invoice → settlement explanation            |

### Deliberate gaps

Bank reconciliation, jurisdiction-specific tax treatment and FX revaluation are outside profile
version 10. The demo promises no documents or UI paths for them.

## Static baseline and live data

The cases above belong to the stable baseline. Live simulation separately adds customer orders and
later invoices and payments. It does not automatically reserve stock, ship, return or replenish
goods, so the reference cases remain reproducible.

The live generator creates zero to six orders per scheduled delivery. Each order is invoiced two to
ten minutes later and carries `DEMO-14-2`. Its deterministic long-run outcome mix is 91% exact, 2%
short with a stated discount, 1% short with freight withheld, 1% paid in two parts, 1% overpaid or
duplicated, 1% unmatched, 2% late and 1% never paid. Exact and late payments may arrive through the
provider or bank path; all exceptions use the bank path. These percentages describe the generator,
not a promise that every small visible sample contains every outcome. Live orders deliberately do
not alter the fixed references above.

## Special evidence and movements

| Source reference                                | What it proves                                                                           | How to inspect it                                                                              |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `wrong-location`                                | 8 × `ITEM-008` are in Singapore, so Rotterdam can still be short                         | Warehouse → Items → `ITEM-008` → stock by location and source evidence                         |
| `shipment-cancelled-remainder`                  | The 2 shipped units of `SO-011` remain physical history after the remainder is cancelled | Sales → Orders → `SO-011` → deliveries/history                                                 |
| `COST-LATE-CLEANUP`                             | A stated 10-unit outbound cleanup leaves 40 × `ITEM-003` in the reviewed layer           | Warehouse → Items → `ITEM-003` → movements; then `SO-024` contribution explanation             |
| `correction-original`, `correction-replacement` | A wrong `ITEM-016` movement is retained and corrected rather than overwritten            | Warehouse → Items → `ITEM-016` → movements/source evidence                                     |
| `history-receipt-*`, `history-shipment-*`       | Each historical sale has both inbound acquisition and outbound shipment evidence         | Open `SO-012`–`SO-023`, then follow the item movement evidence                                 |
| `purchase-receipt-S01`, `S02`, `S04`–`S08`      | Purchase receipts exist only where the scenario says goods arrived                       | Purchasing → Orders → matching `PO-*` → receipts; `PO-003` intentionally has no receipt source |
| `COST-A-SELLING`                                | EUR 114 selling cost for the complete `SO-024` margin story                              | Finance → Payables → search `COST-A-SELLING`; then compare the order's DB2 explanation         |
| `COST-PORTFOLIO-SELLING`                        | Selling-cost allocation across the five portfolio margin cases                           | Finance → Payables → search the reference; compare `SO-025`–`SO-029`                           |

## Which demo mode to use

| Mode                                  | Purpose                                                                                | Start path                                                                                   |
| ------------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| International demo                    | Complete, deterministic reference company documented on this page                      | Companies → New company → Sandbox → Demo company                                             |
| International demo with live data     | Same fixed baseline plus continuous synthetic order-to-cash intake                     | Choose Demo company and enable Live simulation during creation                               |
| Execution fixture (`atlas-execution`) | Small two-item, two-order, one-warehouse practice tenant for bounded execution lessons | Company setup's execution content; intended for guided product exercises, not sales coverage |
| `normal-month` scenario               | CLI-only compact September 2026 story for engineering and service verification         | `reality scenario run normal-month --tenant TENANT_ID`                                       |

## How the four commercial edge cases work

- **Controlled overdelivery:** `SO-039` first promises 10 pcs. Its immutable commitment history then
  records the customer's revised quantity of 12. Only after that statement does the 12-pcs shipment
  pass the normal guard. The original 10 remains visible; without the revision, 12 is refused.
- **Dedicated deposits:** `CDEP-001` is customer money received before the final invoice behind
  `SO-038`; `SDEP-001` is supplier money paid before `SINV-010`. Each clearing is an explicit
  allocation, and each EUR 100 deposit against an EUR 80/100 final invoice leaves the documented
  credit available instead of silently consuming it.
- **Dunning:** `DN-2026-0001` groups one overdue customer invoice at level 2. The operator-stated
  EUR 5 fee is a separate receivable charge, not a mutation of the invoice. No email, automatic
  escalation, automatic collection or invented tax is implied.
- **Bad debt:** the invoice behind `SO-037` receives EUR 60 cash, a separately confirmed EUR 25
  bad-debt expense, and retains EUR 15 open. The adjustment creates no reusable customer credit.

The demo still excludes automatic dunning delivery/runs, jurisdiction-specific tax handling, bank
reconciliation, tax/FX revaluation, manufacturing, payroll and statutory reporting.
