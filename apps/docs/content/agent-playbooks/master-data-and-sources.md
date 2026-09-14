# Playbook: Master data and sources

The data every other playbook stands on: customers, suppliers, items, locations, units, prices,
payment terms, and the systems that deliver records. Nothing here is a business event; it is what
the business has said about itself, and it changes rarely and deliberately. An agent keeps it
current by proposing statements a person confirms. Reality never invents a customer, an item, a unit
relation or a price.

Each situation is one line of context and a few numbered steps: what you pull up, what you say, what
the agent prepares, what you decide, what you check. The tool behind a step stands at the end of its
line after an arrow.

Read [Run a business on Reality with agents](./) first for the loop and the rules.

## What Reality holds and derives

- A Party is a company, a customer or a supplier, and can be several at once (`roles`). It carries a
  default currency, a credit limit, an accounting code, a tax identifier and a default payment term
  code. An Item carries a SKU, a stock unit, an item type (`stocked`, `service`, `charge`), a
  tracking type (`none`, `lot`, `serial`), a lead time and, if the company buys it in another unit,
  a `purchase_unit` with a `conversion_factor`. A Location is a warehouse or a place inside one, in
  a hierarchy. Every record has an opaque id; SKUs, names and codes are what people say, never
  identity.
- Master data is never deleted. `master_data_lifecycle_propose(model, record_id, is_active)`
  deactivates a party, item, location or payment term; history keeps pointing at it.
- A price list has a direction (sales or purchase), a currency and a validity; its tiers state a
  unit price for an item from a minimum quantity, in a unit. `resolve_price` looks at the party's
  own lists by priority, then the lists of the party groups it belongs to, then the default lists,
  and takes the first valid tier. A line whose price is stated freely is ordinary; nothing is
  derived from the absence of a list.
- A payment term is a code with due days and an optional early-payment discount. Invoices name the
  term; from it come the due date behind `overdue_receivable` and the discount that explains a short
  payment. An invoice arriving from a source with a term Reality does not hold fails to interpret
  until the term exists.
- A source system is a registered external system with capabilities: which record types it may
  deliver and what each becomes. Every accepted record is stored losslessly first; interpretation is
  a second step with an outcome (`interpreted`, `needs_review`, `unsupported`, `failed`, ...) that
  `interpretation_coverage` lists with the records it produced. Registration is a declaration of
  allowed intake, not a live connection.
- Reads: `business_records_discover(family="party"|"item"|"location"|"document", query)` finds
  records by name, SKU, code or external id and returns opaque ids.
  `interpretation_coverage( source_record_id?)` shows what became of each source record.
  `exceptions_list` and `exception_explain` carry the three classes below. In the App: Master data
  (customers, suppliers, items, locations), Company → Data → Sources & intake, and Processing.

Exceptions that belong to this area: `units_not_comparable`, `silent_source`,
`source_interpretation_failure`. Master data gaps otherwise show up as refusals at the moment
somebody needs the record, and that is where most of this playbook starts.

The examples use the shop Nordshop as source, the item LAMP-01, the customer Müller GmbH and the
supplier Nordlicht Leuchten GmbH.

## Situations

### Create what a source needs

The shop sent an order Reality could not interpret: a SKU no item carries. Stored losslessly,
waiting.

1. **List:** "Which imports failed?" → Nordshop #1051, "Unknown SKU: LAMP-02" → `exceptions_list` ·
   `source_interpretation_failure` · `interpretation_coverage`
2. **Duplicate?** "Do we have LAMP-02 under another SKU?" → nothing → `business_records_discover`
   `family="item"`
3. **Say:** "Create LAMP-02, desk lamp black, pcs, stocked, from Nordshop product 8841."
4. **Agent:** item with the source as provenance → `item_create_propose` · missing term →
   `payment_term_create_propose` · known item under a new SKU → `item_update_propose`
5. **You:** approve.
6. **Retry and check:** retry the failed job in the App (Processing) → interpreted, order produced →
   `interpretation_coverage` · entry gone

A source order names its customer through the connection, not the payload; unknown items are what
fails.

### Bring master data in from a file

A spreadsheet from the old system: 300 items. Columns are read as given; the file stays the source
every item points to.

1. **Upload** in the App: Company → Data → Sources & intake.
2. **Say:** "Import the uploaded file as items."
3. **Agent:** ingestion with target item; `party`, `location`, `inventory_snapshot` for the other
   kinds; columns `sku`, `name`, `unit`, `purchase_unit`, `conversion_factor`, `lead_time_days` by
   name → `source_ingest_propose`
4. **You:** approve. Existing SKUs are refused, not merged; fix the file and upload again.
5. **Check:** items listed with the file as source → `business_records_discover` · a snapshot shows
   as opening stock → `inventory_read`

### Keep customers, suppliers and items current

Müller gets a higher credit limit and a new default term; a supplier retires. Proposals show before
and after; nothing is deleted.

1. **Find:** "Find Müller GmbH." → credit limit 5,000, term NET14 → `business_records_discover`
   `family="party"`
2. **Say:** "Credit limit 8,000, payment term NET30."
3. **Agent:** update of exactly those fields by opaque id → `party_update_propose` · items and
   locations alike → `item_update_propose`, `location_update_propose` · new records →
   `party_create_propose`, `item_create_propose`
4. **You:** approve; each field from what to what, audited.
5. **Retire:** "Deactivate supplier Altlicht." → `master_data_lifecycle_propose` `model="party"`,
   `is_active=false`; history keeps pointing at it.
6. **Check:** new values → `business_records_discover` · a deactivated party takes no new orders.

### State how units relate

LAMP-01 is bought in boxes of 12, sold by the piece. Until the item says so, six checks skip those
lines silently.

1. **List:** "Which items have units we cannot compare?" → LAMP-01, no conversion, 14 lines on 3
   documents → `exceptions_list` · `units_not_comparable` · `exception_explain`
2. **Which of two:** no relation stated → one statement on the item · relation does not divide
   evenly (107 pieces are not boxes) → correct the line, not the item
3. **Say:** "LAMP-01 is bought in boxes of 12."
4. **Agent:** `purchase_unit="box"`, `conversion_factor="12"` → `item_update_propose`
5. **You:** approve. No unit system; Reality converts only with this factor, at read time.
6. **Check:** entry gone · six classes judge the lines again. Prices are never converted.

### Prices: lists, tiers and who gets which

Müller negotiated 45.00 per lamp from 10 pieces, valid this year. Lists with tiers; assignments
decide who gets which.

1. **Say:** "Sales list KEY-2026, EUR, until 31 December: LAMP-01 45.00 from 10, 48.00 below. Assign
   to Müller, first priority."
2. **Agent:** list → `price_list_create_propose` · tiers → `price_tier_create_propose` · assignment
   → `party_price_list_assign_propose` · groups → `party_group_create_propose`,
   `party_group_member_add_propose`, `group_price_list_assign_propose`. Prices stated, never
   computed.
3. **You:** approve each. Order when several apply: party lists by priority, then group lists, then
   defaults.
4. **Check:** Müller's next agent-prepared order carries the tier (`price_list_entry_id`) · purchase
   side: `invoice_price_differs`, `sold_below_purchase_price`

### Payment terms

Nordlicht offers 2 % within 10 days, 30 net. A code with due days and discount; invoices name it.

1. **Say:** "Create NET30-2: 30 days, 2 % within 10, Nordlicht's default."
2. **Agent:** term → `payment_term_create_propose` `due_days=30`, `discount_percent=2`,
   `discount_days=10` · supplier default → `party_update_propose` · change an existing one →
   `payment_term_update_propose`
3. **You:** approve. Future documents only; recorded ones keep their term.
4. **Check:** next invoice shows due date and discount window → `payment_run_preview` ·
   `purchase_discount_available` · customer side: a short payment equal to the discount is explained
   → `overdue_receivable` tag `early_payment_discount_taken`

### Register a source and what it may deliver

Südshop should deliver orders. Registration declares what the system may state; it is not a live
connection.

1. **Say:** "Register Südshop as a Shopify source for orders."
2. **Agent:** connector shell → `connector_install_propose` `connector_code="shopify"` · no
   connector: `source_system_create_propose` + one `source_capability_create_propose` per record
   type · stop later → `source_capability_lifecycle_propose`, `source_system_lifecycle_propose`
3. **You:** approve. Undeclared capabilities are refused at intake; that is the point.
4. **Connect yourself:** credentials, webhooks, sending live in the shop or your integration layer;
   the connector contract says what a record carries.
5. **Check:** system and capabilities under Sources & intake · first records and their outcome →
   `interpretation_coverage`

### A source went quiet

Nordshop delivers every few minutes and pauses at night. Silent for two days. Nothing broke; figures
are quietly older.

1. **See:** silent → `exceptions_list` · `silent_source` · "Explain it." → last record Tue 22:14,
   longest learned pause 11 h, silent 50 h → `exception_explain`
2. **Ask outside Reality:** shop down, webhook broken, token expired, season over? Records arriving
   is the fix.
3. **Intended silence:** "Deactivate Nordshop's order capability." →
   `source_capability_lifecycle_propose` `is_active=false`
4. **Check:** clears the moment a record arrives · outcome listed → `interpretation_coverage`

A capability with only a handful of deliveries is never reported; no rhythm can be learned from
that.

### Something arrived and could not be understood

A record failed interpretation: unknown SKU, missing term, unsupported type, version conflict. The
record is safe and never edited.

1. **Reason:** "Why did Nordshop #1052 fail?" → "Unknown SKU: LAMP-02" → `interpretation_coverage`
   `source_record_id` · `exception_explain`
2. **Remove the cause:** create the item or term, fix the mapping in the source system, or decide it
   should not be interpreted.
3. **Retry** in the App under Processing; no agent tool for the retry today.
4. **Check:** interpreted → `interpretation_coverage` · entry gone →
   `source_interpretation_failure`, or the next reason.

### A question the records cannot answer

Sales asks "which open orders requested express shipping?" No field holds it. Capture the question
as asked.

1. **Capture:** "Record the question … sales needs it for the daily pick." →
   `reality_gap_create_propose`
2. **Evidence:** "Nordshop payloads carry `shipping_lines.title`, two examples." →
   `reality_gap_entry_add_propose`
3. **Recommend and decide:** a Fact rule over the payload → `reality_gap_recommend_propose`,
   `reality_gap_decide_propose`. See
   [Reality is missing something important](/concepts/business-reality-guide/06-facts-and-open-questions#missing-information).
4. **Check:** decision on the gap → `reality_gaps`, `reality_gap_get` · dry run of an active rule →
   `reality_gap_simulate`

### Review what the sources delivered

The monthly look at every source before the finance handoff.

1. **Ask:** "How did the sources do this month?" → interpreted, needs review, unsupported, failed
   per system and capability; open silent and failure entries; unused capabilities →
   `interpretation_coverage`, `exceptions_list`
2. **Decide:** which failures get a fix, which capabilities are deactivated →
   `source_capability_lifecycle_propose`, which records need review before the handoff.
3. **Next month:** failed and needs-review counts fall; nothing silent that should deliver.

## How an agent should phrase results

- "Item `itm_…` states no purchase unit; 14 lines on 3 documents are not being compared" is a read.
- "Prepared item update: purchase unit box, conversion factor 12; decision `prp_…` pending" is a
  proposal.
- "Approved; `units_not_comparable` no longer lists the item" is verified.
- Never say "created" or "connected" for a proposal that has not been approved, and never present a
  registered source as a live connection.

## Not possible yet

- No unit system: Reality knows what a company states about its own items, not that a kilogram is a
  thousand grams.
- No price conversion between units, and no price proposals; prices are stated from agreements.
- No duplicate detection or merge for parties and items; the agent checks with
  `business_records_discover` before proposing, and a person decides.
- No deletion; lifecycle deactivation only.
- No retry of a failed interpretation through the agent tools; the retry is an App action on the
  failed job.
- No live connection through registration: credentials, webhooks and delivery live in the external
  system or the integration layer.
- Customers are not created from source orders: the connection names the party its orders belong to;
  a shop with many customers needs an integration that resolves them before intake.
