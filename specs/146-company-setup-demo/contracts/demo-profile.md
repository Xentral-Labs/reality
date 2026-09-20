# Canonical International Demo Profile

Status: implemented local profile `international-v2`; no live deployment. Read contracts/capability gaps remain owned by spec 144. No new analytics API is implied.

## Catalog and identity

Use stable synthetic external keys, opaque tenant-local database IDs and English business names independent of UI language. Company party: Harbor Supply. Customers: Northstar Outdoor, Maple Retail, Solstice Living, Pacific Outfitters. Suppliers: Alpine Components, Meridian Textiles, Seabright Goods. Locations: Rotterdam Warehouse (A), Singapore Warehouse (B).

| Key | Item | Unit | Source category |
|---|---|---|---|
| P01 | Summit Bottle | pcs | Outdoor |
| P02 | Trail Lantern | pcs | Outdoor |
| P03 | Ridge Backpack | pcs | Outdoor |
| P04 | Cedar Desk Lamp | pcs | Home |
| P05 | Coast Storage Box | pcs | Home |
| P06 | Harbor Travel Mug | pcs | Outdoor |
| P07 | Aurora Notebook | pcs | Office |
| P08 | Vista Monitor Stand | pcs | Office |
| P09 | Maple Serving Tray | pcs | Home |
| P10 | Orbit Cable Kit | pcs | Office |
| P11 | Meadow Picnic Set | pcs | Outdoor |
| P12 | Beacon Desk Organizer | pcs | Office |
| P13 | Drift Cushion | pcs | Home |
| P14 | Cove Glass Set | pcs | Home |
| P15 | Meridian Fabric | m | Materials |
| P16 | Alpine Wax Pellets | kg | Materials |

Full ready baseline: exactly 16 items, 20 customers, 3 suppliers, 2 stock locations plus 1 company party, with authored settlement on both sides (feature 204): customer payments in three states and six purchase orders from ordered to paid. Seeded orders, invoices and credit notes state an authored buyer per case key (feature 200); a comparison family states one buyer in both windows. Catalog keys are fixture references, never database identity. Source categories remain payload/manifest fields; missing category-query support is disclosed.

## Operational cases at the anchor

Use dedicated P01–P10 items to avoid cross-case allocation interference. Quantities below are expectations derived from the seeded records, not stored operational authority. All demand is at A; B stock must never satisfy A implicitly.

| Case / item | Demand | Matching physical at A after seed | Reserved | Shipped | Condition |
|---|---:|---:|---:|---:|---|
| O01 / P01 | 5 | 10 | 5 | 0 | Future due, healthy |
| O02 / P02 | 5 | 10 | 0 | 0 | Allocation gap, sufficient stock |
| O03 / P03 | 5 | 2 | 0 | 0 | Real shortage |
| O04 / P04 | 5 | 2 | 2 | 0 | Overdue, partly reserved |
| O05 / P05 | 5 | 5 | 5 | 0 | Overdue, fully reserved, unfulfilled |
| O06 / P06 | 5 | 7 | 0 | 3 | Partially fulfilled, 2 still open |
| O07 / P07 | 5 | 10 | 0 | 0 | Explicit hold |
| O08 / P08 | 5 | 0 | 0 | 0 | Overdue + hold + shortage; 8 physically at B |
| O09 / P09 | 5 | 0 | 0 | 5 | Fully fulfilled retained history |
| O10 / P10 | 5 | 10 | 0 | 0 | Cancelled, prior reservation released |

Populate source→document/line→commitment→reservation/movement through shared services. Add purchase commitments for partial overdue receipt, future open supply and unknown-due supply; none is an arrival forecast. Include a correction referencing its original movement, a release and separate unit examples. Keep P01–P10 final totals above unchanged when adding purchasing/correction stories; use the other six items or an explicitly balanced correction sequence.

## Historical comparison

Anchor is explicit UTC midnight (default creation-date midnight). Windows are `[anchor−84d, anchor−42d)` and `[anchor−42d, anchor)`. At least one authored sale in each of 12 weeks, including boundary examples. Every source business date belongs to its intended period; received_at/created_at/audit remain real ingestion time. Operational due cases at anchor remain distinct from history.

Use P11–P16 for historical cohorts so historical movement cannot change O01–O10's stock. All values below are authored fixture inputs; tests read actual source/evidence/postings and compare the declared effects.

| Cohort | Prior | Current | Meaning |
|---|---|---|---|
| Volume / P11 | 10 units at EUR 20 | 20 at EUR 20 | More units, fixed price |
| Price / P12 | 10 at EUR 20 | 10 at EUR 25 | Same units, higher price |
| Decline / P13 | 20 at EUR 15 | 5 at EUR 15 | Lower quantity |
| Credit / P14 | Authored sale | Sale plus explicitly linked credit/return | Credit changes booked amount; physical return separate |
| Outlier / P15 | Ordinary authored activity | One clearly numbered large order/invoice | Outlier is identified, not normalized away |
| Zero prior / P16 | No prior postings | Current activity only | Percentage comparison unavailable |
| USD / P11 | Explicit USD sale | Explicit USD sale | Separate currency, never summed with EUR |

Invoice/order amounts, discounts, tax statements and gross/net basis must be authored explicitly in payloads where supported. Do not invent a cost basis or derive gross into net revenue. The supported posting metric is sales_revenue credits minus debits grouped by currency and posting effective_at; it is neither profit nor payment. Product quantities/prices come from lines; whole-document posting amounts are never allocated repeatedly to every line.

## Minimal integration prerequisites

For a truly empty Sandbox, connection preview offers only P01, P02, P11, P12, the demo customer pool (`DEMO_DATA_CUSTOMERS`: the twenty profile customers), Rotterdam Warehouse and the Harbor Supply company party needed for outgoing commitments, with lossless synthetic master sources. A populated Sandbox reuses existing pool customers and adds the missing ones on connection or Start. No supplier, history, stock, reservation, invoice or payment is added. An existing full canonical profile provides these compatible references. A populated incompatible or incomplete profile fails explicitly rather than silently repairing or remapping. Deterministic arrival vocabulary uses this subset; default missing costs/promotions remain missing.

Baseline source namespace is `demo_profile`; ongoing arrival namespace is `demo_data`, so historical baseline and current intake remain separable. Continuous source identity includes schedule+logical delivery IDs and actual business dates. Optional running source does not change the baseline manifest or execution fixture.

## Manifest and execution

Expose tenant/profile/version/anchor/windows and bounded named case/reference links. Include each relevant area as available, fillable with test data, interface gap or another source, referencing spec 144 assessment. Current/historical prices are supported only through existing authoritative fields; missing costs/promotions/price floors remain absent and no invented margin scenario is presented.

Execution profile has a separate fresh practice tenant, one unit matching free stock and one open unreserved commitment, plus a held refusal case. Its marker disallows Demo Data. No confirmed proposal/receipt is fabricated on setup. Existing actual review/confirmation and receipt verification demonstrate reserved+1, available−1, physical unchanged. Repeating with a fresh request creates a new tenant; same request reuses prior result; earlier analysis and audit survive.

## Bounded costing stories (international-v2)

The canonical baseline adds three named source-backed cases without changing the
ongoing Demo Data generator. `fixture_a` states 1,200 EUR net revenue, 100 pcs and
1,050 EUR acquisition cost; 60 fulfilled and billed pcs are explicitly matched at
630 EUR, while 40 remaining pcs retain 420 EUR acquisition value. DB1 is derived as
570 EUR; 90 EUR direct and 24 EUR allocated source-backed selling costs derive DB2 of
456 EUR (38 %) through the shared contribution read. `missing_cost` deliberately retains quantity and
revenue evidence without a cost review. `late_cost_return` retains the earlier gap,
then adds separately sourced cost and an exact ten-piece customer return/credit match.

All three flow through `demo_profile` SourceRecords and the normal document, movement
and costing services. The fixed initialization recipe uses a transaction/run/owner-bound
authority and ordinary cost proposals/events; it is not available to adapters and grants
no other finance command. Replay never duplicates approvals or restarts a later paused or
stopped Demo Data source. Continuous synthetic orders retain their default missing-cost
semantics and are not advertised as fully costed.
