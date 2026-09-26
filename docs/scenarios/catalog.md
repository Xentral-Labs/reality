# Business Scenario Catalog

Spec impact: none. This is a test-planning inventory; it changes no behavior.

A systematic inventory of B2B and e-commerce situations a company with up to about
EUR 100 million annual revenue meets in practice. Each scenario has a stable ID so tests,
specs and gaps can refer to it. [coverage.md](coverage.md) records, per ID, whether
Business Reality already proves the scenario today and on what evidence.

## How the list is generated

A scenario list stays complete when it is generated, not brainstormed:

1. **Process steps per chain.** Sales: quote → order → release → reservation → picking →
   shipment → invoice → payment → return/credit. Purchasing: demand → purchase order →
   supplier confirmation → advice → receipt → supplier invoice → payment → supplier return.
2. **Every deviation at every step.**

   | Axis | Variants |
   |---|---|
   | Quantity | exact, less, more, zero, in parts |
   | Time | on time, early, late, never, backdated |
   | Value | different price, discount, currency, rounding |
   | Identity | wrong item, wrong party, duplicate, substitute |
   | Order of events | out of order, repeated |
   | Change | amended or cancelled before / after the step |
   | Structure | split, merge |

3. **Crossed with business models:** B2C web shop, marketplace (Amazon FBA/FBM, Otto,
   Zalando), B2B wholesale, EDI retail, drop shipping, subscription, light assembly
   (kits/bills of material), third-party logistics.
4. **Size profile:** several warehouses, several countries (OSS, reverse charge), foreign
   currency, thousands of orders a day, several channels at once, external accounting.
5. **Cross-check sources:** SAP Best Practices scope items (O2C/P2P), the APQC Process
   Classification Framework, EDIFACT messages (ORDERS, ORDCHG, ORDRSP, DESADV, RECADV,
   INVOIC, REMADV), Shopify and Amazon order state models, and real support tickets.
6. **One question per scenario.** The test is not a click path. It is whether Reality
   answers the right question correctly and can explain the answer down to the source.

## Scenario test template

```text
ID / title
Given:     stock, parties, open commitments
Sources:   which SourceRecords arrive, in which order
Reality:   expected Commitments, Reservations, Movements, LedgerEntries, Facts
Questions: what is open, why is it not shipped, who owes whom what
Explain:   the shortest true chain to the original payload
Forbidden: no fulfillment status on documents, no stored derivation as authority
```

Priority = frequency × damage when wrong.

## Coverage legend

- **covered** — a scenario/business-story or service test proves it end to end.
- **partial** — the model supports it, but a test covers only part, or only one side.
- **missing** — the model probably supports it; no test proves it.
- **gap** — the model or services cannot represent it today.
- **out** — deliberately out of scope for the core (state why in coverage.md).

## A. Order intake and order changes

| ID | Scenario | Question Reality must answer |
|---|---|---|
| A01 | Standard order: one customer, one line, in stock | Is it committed, reserved, shipped, invoiced, paid? |
| A02 | Order with 30 lines from several warehouses | What is open per line and per location? |
| A03 | Same item twice in one order (discounted and free) | Are the two lines kept as separate commitments? |
| A04 | Customer raises the quantity after a partial delivery | What is still open after the revision? |
| A05 | Customer lowers the quantity below the delivered quantity | Is the revision refused or does it demand a return? |
| A06 | One line cancelled, the rest stays | Is only that commitment closed and its reservation released? |
| A07 | Whole order cancelled after reservation | Are all reservations released? |
| A08 | Cancelled after picking, before shipment | Does the stock go back, and is that visible? |
| A09 | "Cancelled" after shipment | Is it treated as a return or refusal, not a cancellation? |
| A10 | Customer swaps a variant/size in an open order | Old commitment closed, new one opened, history kept? |
| A11 | Delivery address changes after release, before shipment | Which address does the shipment use, and is the change traceable? |
| A12 | Requested delivery date in the future | When should stock be reserved? |
| A13 | Different requested dates per line | Is each line's promise dated separately? |
| A14 | Quote converted to an order with changed quantities/prices | Are quote and order separate evidence with a link? |
| A15 | Same order arrives twice (webhook retry) | Exactly one commitment? |
| A16 | Shop sends a new version of the same order | New source version, revised commitment, no overwrite? |
| A17 | Shop order contains an unknown item | Is the line kept and the gap visible? |
| A18 | Order price differs from list price | Is the stated price recorded, not recomputed? |
| A19 | Zero-price line (sample, gift, replacement) | Committed and shipped without revenue? |
| A20 | Two orders of one customer to be shipped together | Can one shipment fulfil both? |
| A21 | One order split across two delivery addresses | Can lines/quantities go to different recipients? |
| A22 | Order parked or held (clarification, fraud check) | Why is it not moving, and who lifts it? |
| A23 | Blanket order with call-offs | See M01. |
| A24 | Line added later that should ride with the open shipment | Does the added commitment join the pending delivery? |

## B. Availability, reservation and backorder

| ID | Scenario | Question Reality must answer |
|---|---|---|
| B01 | Too little stock: partial reservation, rest backordered | Reserved vs uncovered quantity per line? |
| B02 | No stock at all | Is the whole commitment uncovered and flagged? |
| B03 | Two orders compete for the last units | Who gets them, by which rule? |
| B04 | Re-reservation to a more important customer | Is the move from one commitment to another traceable? |
| B05 | Stock exists but is blocked (quality, quarantine, expiry) | Is blocked stock excluded from availability? |
| B06 | Stock exists in the wrong warehouse | Is a transfer needed, and is availability per location? |
| B07 | Stock only on order (open purchase) | Can it be promised (available to promise)? |
| B08 | Receipt resolves backorders | Which commitment is served first? |
| B09 | Receipt covers only part of the backorders | Which remain uncovered? |
| B10 | Customer refuses partial delivery | Reserved but deliberately not shipped — why? |
| B11 | Partial delivery allowed up to two parcels | Is the limit enforceable or at least visible? |
| B12 | Reservation lapses because prepayment did not arrive | Is the reservation released after the deadline? |
| B13 | Count difference leaves a reservation uncovered | Is the reservation flagged as no longer backed by stock? |
| B14 | Oversold across channels (shop and marketplace) | Is the overcommitment visible? |
| B15 | Safety stock withheld from B2C, given to key accounts | Can availability differ per channel/party? |
| B16 | Channel quotas (e.g. 20 % for Amazon) | Can stock be earmarked per channel? |
| B17 | Batch/expiry: customer demands minimum remaining shelf life | Is only eligible stock reserved? |
| B18 | Serial-numbered item reserved by serial number | Does the reservation name the unit? |

## C. Payment and release

| ID | Scenario | Question Reality must answer |
|---|---|---|
| C01 | Prepayment: ship only after payment | Why is it held, and when is it released? |
| C02 | Prepayment short-paid | Release or not, within which tolerance? |
| C03 | Prepayment overpaid | Does a customer credit balance appear? |
| C04 | One payment for two prepaid orders | Is the payment allocated to both? |
| C05 | Payment without a usable reference | Unallocated, later allocated by a person? |
| C06 | Payment arrives after the order was cancelled | Is a refund owed? |
| C07 | Credit limit exceeded: order held, released by a person | Who released it, and why? |
| C08 | Limit exceeded by overdue items, not by order value | Does the hold name the overdue items? |
| C09 | Card/PayPal/Klarna: authorization ≠ capture | Are authorization and capture separate facts? |
| C10 | Authorization expires before a late partial shipment | Is the uncovered remainder visible? |
| C11 | B2B invoice with 30 days net, 2 % discount within 10 days | Due dates and discount window correct? |
| C12 | Discount taken after the discount window | Is the short payment flagged? |
| C13 | Cash on delivery | Payment tied to the shipment? |
| C14 | 30 % down payment, rest before shipment | Is the hold released only after the remainder? |
| C15 | Chargeback / returned direct debit after shipment | Does the receivable reopen? |
| C16 | Customer delivery block (dunning, insolvency) | Why does nothing ship to this party? |
| C17 | Fraud check holds and releases an order | Hold and release both recorded? |
| C18 | Voucher or gift card as (part) payment | Is the voucher a settlement of the receivable? |

## D. Picking, shipment, split and merge

| ID | Scenario | Question Reality must answer |
|---|---|---|
| D01 | Partial delivery: 3 of 5 shipped | Open 2, shipped 3? |
| D02 | Two warehouses, two parcels, one order | Movements per location, one commitment? |
| D03 | Several orders of one customer in one shipment | One shipment fulfils several commitments? |
| D04 | Picking error caught before shipment | Corrected without a false movement? |
| D05 | Picking error found by the customer | Wrong item shipped, right item still open? |
| D06 | Picker finds less stock than recorded | Count correction plus uncovered reservation? |
| D07 | Parcel lost, carrier insurance pays | Goods gone, claim receivable, customer still served? |
| D08 | Parcel undeliverable, returns | Stock back, commitment reopened? |
| D09 | Delivery refused | Same as D08 with a reason? |
| D10 | Drop shipping: supplier ships directly | Customer served without own stock movement? |
| D11 | Partial drop shipping: part own stock, part supplier | Both paths fulfil one commitment? |
| D12 | 3PL confirms shipments late | Is the lag visible and later closed? |
| D13 | Pallet freight with booked delivery slot | Shipment dated to the slot? |
| D14 | Export to a third country (customs, proof of export) | Is the export evidence linked? |
| D15 | Customer pickup | Fulfilled without a carrier? |
| D16 | Free replacement shipment without a new order | Why did stock leave, and for which commitment? |
| D17 | Shipment confirmation arrives before the order | Is it held until the order arrives, then linked? |
| D18 | Shipment reported twice | Exactly one movement? |
| D19 | Returnable packaging or deposit (pallets, crates) | Is the deposit owed and tracked? |

## E. Customer invoice and credit note

| ID | Scenario | Question Reality must answer |
|---|---|---|
| E01 | One invoice per partial delivery | Shipped but not invoiced = 0? |
| E02 | Monthly collective invoice over several shipments | One invoice, several deliveries? |
| E03 | Invoice before delivery (prepayment, pro forma) | Invoiced but not shipped visible? |
| E04 | Invoice corrected: reversal plus new invoice | Never overwritten? |
| E05 | Partial credit note without returned goods | Receivable reduced, stock unchanged? |
| E06 | Credit note with returned goods | Both linked to the return? |
| E07 | Invoice differs from the order (quantity/price) | Is the difference visible? |
| E08 | Shipping cost, small-quantity surcharge, payment fees | Charges separate from goods? |
| E09 | Invoice addressed to another party than the recipient | Bill-to ≠ ship-to kept? |
| E10 | E-invoice (XRechnung/ZUGFeRD) | Stored losslessly as a source artifact? |
| E11 | Down-payment invoice and final invoice | Down payment offset in the final invoice? |
| E12 | Rounding difference between lines and total | Stated totals recorded, not recomputed? |

## F. Returns and complaints

| ID | Scenario | Question Reality must answer |
|---|---|---|
| F01 | B2C withdrawal within 14 days, full refund | Stock back, refund owed and paid? |
| F02 | Partial return: 2 of 5 | Returned 2, kept 3? |
| F03 | Different item returned than announced | Announced vs arrived visible? |
| F04 | Unannounced return | Accepted and linked later? |
| F05 | Damaged return, partial refund | Disposition and refund independent? |
| F06 | Mixed disposition: restock, quarantine, scrap, back to supplier | Arrived = sum of dispositions? |
| F07 | Exchange: return plus new delivery, no money | Two commitments, no refund? |
| F08 | Refund before the return arrives (goodwill) | Refund paid, return still expected? |
| F09 | Return announced, never arrives | Stale announcement visible? |
| F10 | Warranty repair via the manufacturer | Goods out and back, ownership clear? |
| F11 | Complaint without return (photo), credit note | Credit without movement? |
| F12 | Marketplace refunds first, goods later or never | Refund and return independent? |
| F13 | Return after month-end for a prior-month invoice | Correct period for the credit? |

## G. Purchasing: demand and purchase order

| ID | Scenario | Question Reality must answer |
|---|---|---|
| G01 | Reorder for a specific customer backorder | Is the purchase linked to the customer commitment? |
| G02 | Reorder for stock at reorder point | Is the demand explained? |
| G03 | Mixed purchase: customer, stock and unassigned | Ordered = assigned + stock + unassigned? |
| G04 | One purchase order with several delivery dates per line | Is each schedule line a separate promise? |
| G05 | Purchase against a supplier framework agreement | Call-offs against a contract? |
| G06 | Minimum order quantity / pack size forces more | Surplus visible as stock-bound? |
| G07 | Tiered purchase prices | Stated price recorded? |
| G08 | Purchase order in foreign currency (USD, CNY) | Currency kept, conversion at posting? |
| G09 | Supplier confirms different quantity/price/date | Confirmed vs ordered visible? |
| G10 | Supplier never confirms | Unconfirmed purchase flagged? |
| G11 | Supplier moves the date several times | Revision history and latest promise? |
| G12 | Purchase cancelled after supplier produced | Cancellation cost or refusal recorded? |
| G13 | Purchase reduced after the customer order was cancelled | Demand chain updated? |
| G14 | Two suppliers for the same item, split sourcing | Both purchases cover one demand? |
| G15 | Drop-ship purchase order for a customer order | Linked to the sales commitment? |
| G16 | Import by sea (8 weeks), one container, many purchases | In-transit per purchase? |
| G17 | Purchase of non-stock items (service, consumables) | No stock movement expected? |

## H. Goods receipt and supplier deviations

| ID | Scenario | Question Reality must answer |
|---|---|---|
| H01 | Receipt exactly as ordered | Purchase fulfilled? |
| H02 | Under-delivery, rest later | Open remainder? |
| H03 | Under-delivery, rest never | Remainder closed by a person with a reason? |
| H04 | Over-delivery accepted | Surplus visible? |
| H05 | Over-delivery rejected or returned | Supplier return linked? |
| H06 | Wrong item delivered | Received item ≠ ordered item visible? |
| H07 | Substitute/successor item delivered | Accepted against the purchase with a link? |
| H08 | Damaged goods, part to quarantine | Quarantine not available? |
| H09 | Receipt without purchase order (free, sample, misdelivery) | Why did stock arrive? |
| H10 | One delivery for several purchase orders | Split across purchases? |
| H11 | Delivery earlier than confirmed | Early receipt recorded? |
| H12 | Receipt recorded before the purchase order exists | Linked later? |
| H13 | Receipt with batches, expiry, serial numbers | Recorded per lot? |
| H14 | Wrong receipt recorded, then corrected | Reversal movement, not overwrite? |
| H15 | Quality inspection releases days later | Received but not released? |
| H16 | Receipt for a customer-specific purchase (cross-docking) | Goes straight to the waiting commitment? |
| H17 | Advice says 100, 96 arrive | Advised vs received visible? |
| H18 | Return to supplier with supplier credit | Movement and credit linked? |
| H19 | Freight and duty arrive later and change landed cost | Cost re-allocated to the receipt? |

## I. Supplier invoice and payment

| ID | Scenario | Question Reality must answer |
|---|---|---|
| I01 | Three-way match: purchase = receipt = invoice | Match confirmed? |
| I02 | Invoiced quantity > received quantity | Difference flagged? |
| I03 | Invoiced price ≠ purchase price | Price variance flagged? |
| I04 | Invoice before receipt | Invoiced but not received visible? |
| I05 | One invoice for several purchase orders | Allocated per purchase? |
| I06 | Several partial invoices for one purchase | Sum vs purchase? |
| I07 | Freight invoice from a third party for a purchase | Linked to the receipt cost? |
| I08 | Supplier credit note for defective goods | Payable reduced? |
| I09 | Down payment to the supplier before production | Prepayment offset later? |
| I10 | Payment with discount; partial payment; offset with credit | Settlement allocations correct? |
| I11 | Exchange difference between USD invoice and payment | FX difference posted? |
| I12 | Duplicate supplier invoice | Detected, not double-posted? |

## J. Warehouse and stock

| ID | Scenario | Question Reality must answer |
|---|---|---|
| J01 | Transfer between warehouses with transit time | Stock in transit? |
| J02 | Stock count with gains and losses | Count movements with reason? |
| J03 | Cycle count of single bins during operation | Correct during open picks? |
| J04 | Shrinkage, theft, breakage with reason | Movement with reason? |
| J05 | Expired stock blocked and scrapped | Excluded from availability, then scrapped? |
| J06 | Negative stock because shipment was booked before receipt | Negative visible and explained? |
| J07 | 3PL stock differs from own records | Reconciliation difference visible? |
| J08 | Consignment stock at the customer (still ours) | Owned but elsewhere? |
| J09 | Consignment from the supplier (here, not ours) | Held but not owned? |
| J10 | Stock valuation after a freight surcharge | Valuation re-derived? |
| J11 | Re-labelling item A into item B | Paired movements? |

## K. Kits, bills of material and variants

| ID | Scenario | Question Reality must answer |
|---|---|---|
| K01 | Kit sold, shipped from components | Availability = minimum of components? |
| K02 | One component missing, no partial kit allowed | Whole kit held? |
| K03 | Return of a single component from a kit | Component back, kit credit partial? |
| K04 | Light assembly: components consumed, finished item produced | Paired movements? |
| K05 | Variant item (size/colour) purchased together | Per-variant stock? |
| K06 | Bundle price split across components (revenue, tax) | Split stated or derived? |

## L. E-commerce and marketplaces

| ID | Scenario | Question Reality must answer |
|---|---|---|
| L01 | Amazon FBA: stock at Amazon, sales/returns/fees via reports | Stock at an external location? |
| L02 | Marketplace order shipped by us with a deadline | Deadline at risk visible? |
| L03 | Marketplace payout: one payment for hundreds of orders minus fees and refunds | Each order settled, fees as charges? |
| L04 | Shopify order partially refunded in the shop | Refund recorded from the source? |
| L05 | Shopify order edited after import | New version, revised commitment? |
| L06 | Pre-order of an item not yet available | Commitment without stock, dated? |
| L07 | Black Friday: 10,000 orders in two hours | Throughput and correct reservations? |
| L08 | Subscription order, payment fails | Recurring commitment held? |
| L09 | Promotion: free item above EUR 50 | Zero-price line? |
| L10 | Guest order, later with an account (duplicate party) | Parties merged, history kept? |
| L11 | OSS: EU consumer, destination-country VAT | Tax rate as stated by the source? |
| L12 | Shipment to Switzerland/UK (customs, DDP/DAP) | Duties and incoterm recorded? |

## M. B2B specifics

| ID | Scenario | Question Reality must answer |
|---|---|---|
| M01 | Blanket order for 10,000 units with monthly call-offs | Called off vs remaining? |
| M02 | Customer-specific prices, item numbers and names | Customer item number maps to our item? |
| M03 | EDI chain ORDERS → ORDRSP → DESADV → INVOIC → REMADV | Each message a source, linked? |
| M04 | ORDCHG after confirmation | Revised commitment? |
| M05 | Retail chain: central warehouse plus store delivery | Several recipients per order? |
| M06 | Customer rule: cancel backorders instead of delivering later | Remainder closed by rule with reason? |
| M07 | Customer-prescribed delivery note or pallet label | Out of core scope? |
| M08 | Customer deducts penalty or marketing contribution | Short payment with reason? |
| M09 | Annual rebate at year end | Rebate credit? |
| M10 | Orderer, recipient, bill-to and payer are four parties | Roles kept separate? |
| M11 | Customer is also a supplier (netting) | Receivable and payable offset? |
| M12 | Sample or loan with return obligation | Goods out, return expected? |

## N. Finance, tax and currency

| ID | Scenario | Question Reality must answer |
|---|---|---|
| N01 | Intra-community supply (VAT-exempt, VAT ID) | Stated tax recorded? |
| N02 | Reverse charge on purchase | Stated tax recorded? |
| N03 | Sale in CHF or USD, payment in EUR | Currency and FX difference? |
| N04 | Dunning in three levels, then collection | Dunning notices from open items? |
| N05 | Bad debt write-off | Receivable closed with reason? |
| N06 | Open items per party incl. credits and prepayments | Party balance correct? |
| N07 | Handover to DATEV/external accounting, later correction | Reversal after export? |
| N08 | VAT rate change at a cut-off date | Rate per invoice date? |

## O. Master data and identity

| ID | Scenario | Question Reality must answer |
|---|---|---|
| O01 | Item number renamed | History intact (numbers are not identity)? |
| O02 | Two parties merged as duplicates | History of both kept? |
| O03 | Customer moves; old orders keep the old address | Address as stated per document? |
| O04 | Item delisted with open orders or purchases | Open commitments still served? |
| O05 | Unit conversion: buy in cartons of 12, sell in pieces | Quantities comparable? |
| O06 | Supplier item number ≠ own number, several suppliers | Supplier item mapping? |

## P. Sources and integration

| ID | Scenario | Question Reality must answer |
|---|---|---|
| P01 | Same event delivered twice | Idempotent? |
| P02 | Events out of order | Linked correctly once complete? |
| P03 | Source corrects an earlier record | New version, not overwrite? |
| P04 | Source deletes an order afterwards | Commitment closed with source reason? |
| P05 | Incomplete payload accepted | Gap visible? |
| P06 | Two systems contradict each other | Contradiction visible? |
| P07 | Integration down for a day, then catches up | No duplicates, silent source detected? |
| P08 | Legacy import at go-live (opening stock, open items, open orders) | Opening balances traceable? |

## Q. Time and period

| ID | Scenario | Question Reality must answer |
|---|---|---|
| Q01 | Month-end: shipped not invoiced, invoiced not shipped | Both lists correct? |
| Q02 | Backdated posting into a closed period | Refused or flagged? |
| Q03 | Stock as of 31 December | Point-in-time stock? |
| Q04 | Year end with open backorders and purchases | Carried over correctly? |
| Q05 | Time zones: order at 23:30 in New York | Stored in UTC, dated correctly? |

## R. Combined stress stories

| ID | Scenario | Question Reality must answer |
|---|---|---|
| R01 | Customer orders 10, 4 in stock, prepayment 80 % paid, released anyway, 4 shipped; 6 reordered, supplier delivers 5 in two dates; customer cancels 1; rest shipped; 2 returned damaged | Every quantity and every euro reconciles at the end. |
| R02 | Two customers wait for one item; under-delivery; key customer re-reserved; the other cancels | Cancelled demand leaves the purchase assignment. |
| R03 | Drop shipment with wrong item; customer returns it to us instead of the supplier | Ownership and credits on both sides. |
| R04 | Marketplace payout with 400 orders, 12 refunds, 3 chargebacks and fees | Every position allocated. |
| R05 | EDI customer sends ORDCHG after a partial delivery was advised | Revision respects what already shipped. |
| R06 | Import container: 5 purchases, 2 suppliers, freight, duty, USD rate; 2 customer orders waiting | Landed cost and customer allocation. |
| R07 | Month-end count difference uncovers three reservations | Who is postponed, and how is it explained? |
| R08 | Customer is also a supplier, with an overdue receivable, an open credit and a new order above the credit limit | Hold reason names all facts. |
