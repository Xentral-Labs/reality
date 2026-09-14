# Idea: Demo Data pays its orders — synthetic order-to-cash

**Status:** specified and implemented as [feature 168](../../specs/168-demo-order-to-cash/spec.md)
on 2026-09-10; kept as the record of the reasoning and the owner's decisions.

## Problem

Demo Data (spec 146) creates one synthetic sales order per scheduled occurrence and
stops there. FR-018 says incoming demand must not automatically execute payments, and the
demo-data contract repeats it: "Source activity never reserves, fulfills, ships, pays or
replenishes." The result is a company whose order list grows while Open Items, Payments,
the Journal and the customer credit view stay frozen at the seeded 84-day baseline.

Visitors therefore never see the part of Reality that is hardest to fake: money arriving
against invoices, most of it exact, some of it short, late or too much, and every
difference explainable down to the bank line. The finance work of spec 148 (available
credit, accepted reductions, money paths) has nothing continuous to act on.

## Target picture

A running demo company should look like a small B2B/e-commerce merchant whose shop,
billing system, payment provider and bank keep sending evidence:

```text
order (exists today)
  -> invoice for the order            synthetic billing evidence, posted
  -> customer payment                 synthetic bank line or provider capture
       exact          most of the time, allocated to the invoice, invoice settled
       short          residual stays open: claimed discount, withheld freight, partial
       over           invoice settled, excess becomes available customer credit
       late           arrives after the due date, aging register shows it first
       unmatched      reference missing/wrong: recorded, unallocated, needs matching
       never          stays open and becomes overdue
  -> (later stage) provider fee and payout to the bank account
```

Everything the simulator emits is source evidence that travels the normal intake path.
Reality decides what it means with the same services a real bank import would use.
Nothing in this plan writes a LedgerEntry, allocation or document directly from the job.

## What real e-commerce looks like, roughly

The weights below are the proposal for the profile constants. They are rounded from
general industry experience (DACH online retail and B2B wholesale receivables), not from a
cited dataset, and they are deliberately tunable in one table in the producer module.

### Money path per order

| Path | Share | Behaviour |
|---|---|---|
| Provider capture (card, PayPal, wallet, BNPL) | 60 % | Amount always exact; arrives minutes after the order |
| Bank transfer (prepayment or purchase on account) | 40 % | Customer types the amount; this is where differences live |

### Outcome per order

| Outcome | Share of all orders | Detail |
|---|---|---|
| Exact and on time | 91 % | One payment equal to the invoice total, within terms |
| Short: claimed early-payment discount | 2 % | 2–3 % deducted, reference names "Skonto"/"discount" |
| Short: withheld small amount | 1 % | Freight or rounding difference, 0.50–6.00 |
| Short: genuine partial, rest follows | 1 % | Second payment closes the invoice later |
| Over: duplicate or typo | 1 % | Second identical payment, or amount rounded up |
| Unmatched reference | 1 % | Correct amount, reference missing or points at the order number |
| Late but paid | 2 % | Arrives after the due date |
| Not paid within the demo window | 1 % | No payment record is ever produced |

So roughly one order in ten needs a human look, which is what a real accounts-receivable
desk sees, and nine in ten settle silently. Differences only occur on the bank-transfer
path; provider captures are exact by construction.

Every choice is derived from `sha256(seed, schedule_id, delivery_id, step)` exactly like the
current product/customer choice, so a run is reproducible and a retry never changes its
mind. A test over ten thousand seeded orders must land within a tolerance of the table.

## Timing under wall-clock rules

Spec 146 forbids an accelerated clock and backdated business timestamps. Payments therefore
arrive with compressed but ordered delays after the order:

| Step | Delay after the previous step |
|---|---|
| Invoice issued | 2–10 minutes after the order |
| Provider capture | 1–3 minutes after the invoice |
| Bank transfer | 10–90 minutes after the invoice |
| Second payment (partial rest, duplicate) | 20–120 minutes after the first |
| Late payment | after the stated due date |

The invoice states a real payment term (default 14 days, `payment_term_code` already exists
on documents through spec 088). Consequence: "late" and "overdue" become visible only on a
demo that runs longer than the term, such as the Railway demo. See decision 1 for the
alternative of shorter synthetic terms.

## Architecture

### 1. Synthetic source: two new record types

`integrations/demo_data.py` gains two producers next to `produce`:

- `plan(seed, schedule_id, delivery_id) -> OrderToCashPlan`: pure function returning money
  path, outcome, delays, amounts and the reference text the payer will write. Unit-tested
  in isolation; the only place where the weight tables live.
- `produce_invoice(order_payload, plan, at)`: lossless invoice payload with schema version,
  `synthetic: true`, `order_external_id`, invoice number, issue date, due date, payment term
  code, currency, source-stated gross/tax/discount and lines that name the order line they
  bill.
- `produce_payment(order_payload, invoice_payload, plan, n, at)`: bank-line or
  provider-capture payload with `money_path`, amount, currency, `paid_at`, payer party,
  the typed references the payer or provider states (invoice number, shop id, shop order
  number, customer reference or customer number; correct, partial, wrong or empty according
  to the plan) and the logical payment index `n`.
- The existing order payload gains a separate synthetic shop id beside its readable order
  number and a customer reference, so the three identifier roles exist to be resolved.

External identities stay stable and stateless:

```text
order    {schedule_id}:{run_id}                (exists)
invoice  {schedule_id}:{run_id}:invoice
payment  {schedule_id}:{run_id}:payment:{n}
```

The source system `demo_data` receives two more capabilities: `invoice -> sales_invoice`
and `payment -> payment`. Its catalog text changes from "Synthetic incoming orders" to
synthetic orders, invoices and customer payments. Still no credentials, still no provider
claim.

### 2. Shared interpretation core: the path Stripe and PayPal will take later

Orders already enter Reality the way a Shopify webhook will: `enqueue_source`, an
ImportJob, a registered interpreter in `SOURCE_INTERPRETERS`, shared document and
commitment services. Payments have no such path at all today. No provider interpreter
exists, the connector catalog only declares empty shells for Stripe, Shopify Payments and
PayPal, and the one external payment intake, the bank-statement CSV profile, records money
without ever allocating it. The demo payment interpreter is therefore the first of its kind,
and it must be built as the shared consumer, not as a demo special case.

The design is two layers per record kind:

```text
provider payload  -> normaliser (per source)     -> normalised evidence -> shared core
Demo bank line       demo_data.payment               NormalisedPayment     interpret_customer_payment
Stripe charge        stripe.charge        (later)
PayPal sale          paypal.sale          (later)
Shopify transaction  shopify_payments.transaction (later)

Demo invoice         demo_data.invoice               NormalisedInvoice     interpret_sales_invoice
Billing system X     (later)
```

**Shared core, provider-agnostic, lives in `services/`:**

- `interpret_sales_invoice(session, tenant_id, source, normalised)`: resolve the billed
  order lines by source identity, create the `sales_invoice` with
  `create_manual_document_with_lines`, set `billed_document_line_id` per line (spec 076),
  attach the payment term, post it (spec 091). Replay returns the existing document.
- `interpret_customer_payment(session, tenant_id, source, normalised)`: record the payment
  with `record_customer_payment` and the source record, resolve the remittance reference to
  at most one posted invoice of the same party and currency, allocate
  `min(amount, open_invoice_amount)` with `allocate_settlement`, leave the rest as
  unallocated credit. No match: record only. The core never over-allocates, writes off,
  accepts a discount or invents an invoice.
- Both return the same reference structure the order interpreter returns today, so
  interpretation outcomes, business events and the inspector links need no new shape.

**Normalised shapes** are small Pydantic models with only the fields the core acts on:
payer party, amount, currency, effective time, external payment identity, reference text,
money path, and for invoices the order identity, lines, term and dates. Everything else
stays in the lossless payload. The field names follow the existing `bank_statement`
file profile so a synthetic bank line, an imported CSV line and a later provider event
look alike to the core.

**Normalisers** are thin and per source. The demo one validates the synthetic payload and
maps it one to one. A Stripe normaliser would later map a charge's customer, amount,
currency, `metadata.invoice_number` and balance transaction into the same shape and register
`("stripe", "charge")` in `SOURCE_INTERPRETERS`. Nothing in the core changes for that.

#### Matching: three tiers, and who decides

The durable form of this section is the proposed contract
[docs/features/payment_matching.md](../features/payment_matching.md); the reading copy for
ERP users is drafted in [payment-matching-guide/](payment-matching-guide/payments-and-matching.md).

Nothing in Reality matches payments today. The plan adds matching as three separated
tiers. Reality performs the first two itself, deterministically; the third is a proposal
that a person or an agent confirms.

1. **Record, always, without a decision.** Every incoming payment becomes a payment
   document and a cash-against-receivable posting with its source record. Nothing is
   interpreted, nothing can be mis-allocated, and the money is visible from that moment even
   when nobody knows what it belongs to. This is what the bank-statement CSV path already
   does.
2. **Allocate, only when the source states the link.** Reality allocates automatically when
   the reference is stated by the source, never when it would have to be guessed
   (constitution rule 11). Party and currency must match and exactly one posted invoice must
   result; then `min(amount, open)` is allocated. Exact, short and over payments are all
   allocated this way. The difference stays visible as an open residual or as customer
   credit, and what happens to it (accept a discount, leave open, refund) is the confirmed
   human action of the spec 148 payment-differences contract. No tolerance silently writes
   off small amounts.
3. **Propose, when no link is stated.** Without a stated or unambiguous reference Reality
   allocates nothing. It computes candidates at read time: same party, same currency, amount
   equal to the open amount of exactly one invoice, or an invoice number as a substring of
   the remittance text. Candidates are shown in Payments and over MCP with the reason they
   fit. They are never stored (spec 148: suggestions are read-time observations that require
   confirmation). Confirmation runs through the existing propose-and-execute tools, which
   call `allocate_settlement`.

An external agent is optional, not required. Chat and MCP call the same tools as CLI and
Web, and every mutating action needs confirmation. An agent may review tier-3 candidates
and present them for confirmation with its reasoning, or confirm them itself where the
tenant allows that. It receives the same candidates a person sees and owns no matching
logic of its own, so every allocation stays explainable regardless of who triggered it.

Most e-commerce money is provider money carrying the shop order identity, plus bank
transfers with a clean invoice number; both flow through tier 2 silently. What remains is
the small share without or with a wrong reference, about one order in a hundred in the
profile above, plus the difference cases. Those are what the UI shows and where an agent
earns its place. A fuzzy tier 2 would occasionally allocate wrongly, and a wrong allocation
costs more than an open one.

#### Identifiers: which number resolves to what

One order carries several numbers, and the resolver must know the role of each. Reality
mints no numbering series of its own; a document's `number` is what the source stated
(constitution rule 6: human numbers are never identity). Today's Shopify interpreter stores
the shop's numeric `order.id` as the SourceRecord `external_id` and the shop's order name
(`#1001`) as the document `number`; the customer's own purchase-order number has its own
field `customer_reference`. When a real ERP later sits in front of Reality, its order number
arrives as `number` and the shop number as a second reference.

On the payment side the provider transaction id (Stripe charge, PayPal transaction, Shopify
transaction) is the identity of the payment itself and becomes the payment SourceRecord's
`external_id`; it says nothing about what the money is for. The link that matters is the
provider's reference to the order (Stripe `metadata`, PayPal `invoice_id`/`custom`, Shopify
transaction `order_id`), which almost always names the shop id or shop number, never an
invoice. A bank remittance is free text that may carry an invoice number, an order number,
a customer number, the customer's PO number, or nothing. A customer number (the existing
`party_accounting_code` of the bank-statement profile) identifies the party, not an invoice.

The normaliser therefore extracts a list of typed references as the source stated them, and
the core resolves them:

| Reference type | Looked up in | Path to the invoice |
|---|---|---|
| Invoice number | `number` of the party's posted sales invoices | direct |
| Shop id | `external_id` of the order SourceRecord in the matching source system | order, then `billed_document_line_id` to the invoice |
| Shop order number | `number` of the party's sales orders | order, then invoice |
| Customer reference / PO | `customer_reference` of the party's sales orders | order, then invoice |
| Customer number | party | no invoice; narrows candidates only, so tier 3 |

Tier 2 allocates only when exactly one posted invoice results. Two invoices for one order
(partial billing) or one invoice covering several orders (consolidated billing) are not
errors but not unambiguous either; they go to tier 3 with their candidates. The remittance
text is retained verbatim; the allocation itself remains, as today, an opaque link between
two ledger entries. Numbers are used to look up, never stored as the link.

Consequences for the synthetic source: the order payload carries a shop id and a shop order
number as separate values so the provider path realistically resolves through the id and
the bank path through invoice or order number, and the "unmatched" cases imitate the
typical real mistakes: customer number only, the customer's own PO number with no order
behind it, or a typo in the invoice number.

This keeps the boundary the simulator idea insists on: the producer (`integrations/`) shares
no parsing code with the consumer (`services/`). Only the consumer is shared between demo
and future providers, which is exactly where sharing is wanted.

Two realism gaps stay open and are named, not hidden. There is no webhook endpoint yet, so
transport, signature and binding behaviour are not exercised by the demo; that remains the
simulator idea's scope. And the demo payload carries internal item and party identities
where a real provider payload carries SKUs and customer references that need mapping, so
the mapping step is not exercised either.

### 3. Registered demo interpreters and the automation authority

Registered in `SOURCE_INTERPRETERS` beside `("demo_data", "order")`:

- `("demo_data", "invoice")`: demo normaliser, then `interpret_sales_invoice`.
- `("demo_data", "payment")`: demo normaliser, then `interpret_customer_payment`.

  Two details the code dictates. The invoice-bound `post_customer_payment` refuses any
  amount above the open receivable, so the interpreter composes the unbounded standalone
  recording with a bounded allocation instead, and it must pin the payment to the invoice's
  own control account (`_settlement_control_entry(...).account_id`) or the allocation is
  rejected for account mismatch. And no reference matching exists anywhere today:
  `payment_number` is a display field. The core therefore needs one small resolver,
  exact invoice number among the payer's posted invoices, not a matching engine.

Rules the interpreter must never break, because they are the point of the demo:

- Never over-allocate, never write off a residual, never accept a discount, never create
  a credit note or refund. Those stay confirmed human actions in the Payments and Open
  Items views (spec 148 payment-differences contract).
- Never invent an invoice for a payment that has none, and never match by amount or date.
  An unmatched payment is an honest unmatched payment.
- Same savepoint discipline as today: `process_import_job_bound` generalises from the
  single `("demo_data", "order")` branch to the three synthetic types; expected validation
  failures keep the source and a failed outcome, unexpected errors roll the occurrence back.

This is exactly the "explicit bounded automation authority" spec 148 reserves for
translation-triggered recording. The authority is bound to the synthetic source in
`require_demo_intake` and to the practice tenant, and it covers posting an invoice the
billing source states and allocating money whose reference is unambiguous. It covers
nothing else.

Three gates block this today and must be opened in this order:

1. **Prose**: spec 146 FR-018, SC-009 and the demo-data contract sentence "Source activity
   never ... pays" need an explicit amendment.
2. **Policy**: `_INTAKE_OPERATIONS` in `tenant_policy.py` is a closed set (store, enqueue,
   process, manual document with lines, commitment, business event). Posting and allocating
   need a second narrow scope for the settlement job, modelled on `_PROFILE_OPERATIONS`,
   which already lets one-time profile initialisation post invoices and ledger groups.
3. **Code**: `process_import_job_bound` is hard-coded to `("demo_data", "order")`, and the
   demo counters filter on `source_type == "order"`; both generalise to the three types.

Two rules from neighbouring specs carry over unchanged. Stated amounts only: the plan
writes the short or excess amount into the payload as a fact, because spec 088 forbids any
service from multiplying a gross amount by a discount rate and a test walks the syntax tree
to enforce it. And the differences surface through existing exception classes without new
rules: an unallocated remainder raises `unmatched_financial_event`, a late or never-paid
invoice raises `overdue_receivable`, and a short payment that fits the invoice's discount
terms carries the `early_payment_discount_taken` tag. For that last one the synthetic
invoice must reference a payment term with a discount window, so the profile needs one
such term (for example 14 days net, 2 % within 7 days) created or matched on connect.

### 4. Scheduling: one more durable schedule, no new business state

Today one schedule runs `demo.generate_orders` every 360/60/12 seconds. The plan adds a
second job definition `demo.settle_orders`, version 1, on a fixed interval of 60 seconds,
created and cancelled together with the order schedule by the existing `control` actions
(start, pause, resume, stop, disconnect, set_rate leaves it alone).

Each occurrence:

1. Authorises exactly like `generate` (eligible owner, connection, source active, matching
   references, running state).
2. Selects the connection's synthetic orders whose plan says an invoice or payment is due
   at or before the occurrence time and whose external identity has no SourceRecord yet.
   Due time is `ordered_at` from the order payload plus the plan's delays, recomputed from
   the seed; the existence of the SourceRecord is the only idempotency marker. No table
   remembers "planned payments".
3. Emits at most a bounded batch (proposal: 10 records) through `enqueue_source` and the
   bound processor, oldest due first. Whatever does not fit waits for the next minute; no
   catch-up burst after a pause because paused time simply shifts nothing: due times are
   absolute, and the batch bound throttles the backlog.
4. Respects the existing saturation rule: 20 pending or failed imports pause the whole
   connection, both schedules.

`DemoDataConnection` gets one nullable `settlement_schedule_id` column (migration plus
`data_model.yaml`). Alternative without schema: fold settlement into the order job. That
couples payment cadence to the order rate and breaks the contract sentence "one scheduled
occurrence creates at most one SourceRecord". See decision 2.

### 5. Money accounts: where the cash lands

Stage A and B post every payment to the tenant's default `cash` role account from the
spec 148 first slice. Practice companies already receive the five reference accounts, so
the Demo Data preview only has to confirm they exist and are not blocked; connect refuses
otherwise with the existing "not compatible" message.

Stage C, once spec 148 money paths are implemented, splits the two paths the way real
books do: provider captures credit the receivable against a provider clearing account,
a separate synthetic provider statement states the fee, and a daily synthetic payout moves
the net amount to the bank account where a synthetic bank line confirms it. Until then the
payload already carries `money_path`, so the same records can be re-read later without
re-emitting them.

### 6. Status, cockpit and UI

- `demo_data.status` grows an `order_to_cash` block: invoices issued, payments received,
  allocated, settled invoices, open residuals, available customer credit created,
  unmatched payments, last settlement time. All counts are observations over source
  records and read services, never persisted.
- `DemoDataIntegration` in App and Playground shows that block under the existing
  counters, with links into Payments (V03), Open Items and the Journal filtered to the
  synthetic source. Preview and catalog copy mention invoices and payments.
- No new operational rule in the web layer: the cockpit's open items, aging register,
  payment differences and available-credit views simply start moving.
- Localisation in the four languages, contract tests for the new status shape, one
  browser script case.

### 7. Catalogs and documents to touch

`connector_catalog.yaml` (two capabilities), `business_event_catalog.yaml` (interpreted
outcomes for the new types), `tenant_isolation_catalog.yaml` (new column and queries),
`data_model.yaml`, `docs/SPEC_COVERAGE_MATRIX.md`, `docs/features/company-setup-demo.md`,
`specs/146-company-setup-demo/contracts/demo-data.md`, and a cross-link from
`integration-simulator.md`, which this plan partly realises for the payment lifecycle.

## Tests, planned before code

- Unit: plan determinism (same inputs, same plan), weight distribution over 10,000 seeded
  orders within tolerance, delay ordering, payload schemas reject missing or negative
  fields, reference text variants.
- Service, shared core: `interpret_sales_invoice` links every line to its order line and
  posts once; `interpret_customer_payment` for exact, short, over, unmatched, second
  payment, wrong currency, wrong party, replay of the same source, retry after a failed
  outcome; allocation never exceeds open amount; savepoint rollback on validation failure.
  These tests feed the core normalised evidence directly, so a later Stripe normaliser only
  adds mapping tests, not behaviour tests.
- Service, matching: each reference type resolves along the table; two invoices for one
  order and a consolidated invoice produce candidates, not an allocation; a customer number
  alone never allocates; candidates are recomputed at read time and never persisted; the
  confirmed tier-3 allocation runs through the existing proposal tools.
- Service, demo normaliser: synthetic payload to normalised shape, one to one, rejects
  unknown schema versions and a missing synthetic marker.
- Job: authorisation refusals, both schedules created and cancelled by every control
  action, batch bound, idempotent identities across retries, saturation pauses both, no
  burst after pause, `set_rate` does not touch the settlement schedule.
- Business story: order → invoice → 980 paid leaves 20 open and the aging register shows
  it; 1,020 paid settles the invoice and shows 20 available credit; unmatched payment shows
  in Payments without an invoice; a later human "accept small remainder" (spec 148) closes
  the short case.
- Adapter: status contract for App and Playground routes, web contract test, browser
  script, localisation audit.
- Migration round trip and tenant isolation for the new column.

## Delivery stages

| Stage | Content | Depends on |
|---|---|---|
| A | Invoice producer/interpreter, exact bank payments, allocation, second schedule, status block | spec 148 first slice (accounts) — merged |
| B | Full outcome table: short, over, unmatched, late, never, second payments; UI block; browser test | A |
| C | Provider path: clearing account, fees, payouts, bank confirmation | spec 148 money paths (not started) |
| D (optional) | Returns → credit notes → refunds; dunning candidates | B, spec 099/082 return contracts |

Stage A alone already makes Open Items and the Journal move and is the smallest coherent
slice; stage B is where the demo becomes convincing.

## Decisions taken on 2026-09-10

The owner took all seven decisions on the recommended option. They are binding input for the
specification; the alternatives are kept for the record.

| # | Decision | Chosen | Rejected alternative |
|---|---|---|---|
| 1 | Payment terms on the synthetic invoice | 14 days net, 2 % discount within 7 days, so discount explanations fire and the aging register stays real; overdue appears only on long-running demos | a 1-day demo term, or a profile-selectable term |
| 2 | Settlement cadence | Second schedule `demo.settle_orders` at 60 s with one new column `settlement_schedule_id`; the 146 contract sentence "one record per occurrence" stays true | folding settlement into the order job |
| 3 | Automation authority | Yes, narrowly: a new intake scope may post the stated invoice, record payments and allocate only unambiguously stated references; reductions, refunds, write-offs and candidates stay confirmed actions. FR-018 and SC-009 are amended | record only; or keep FR-018 unchanged |
| 4 | Who issues the invoice | The synthetic source, as a billing-system evidence interpreted through the shared core | a new Reality service creating invoices from orders |
| 5 | Weight table | Version 1 as tabled above: 91 % exact, 4 % short, 1 % over, 1 % unmatched, 2 % late, 1 % never; 60 % provider, 40 % bank transfer | exaggerated demo mix |
| 6 | Shared core placement | New module `services/payment_intake.py` holding cores, normalised shapes and the resolver | more functions in `services/core.py` |
| 7 | Base checkout | `.claude/worktrees/invoice-lines-research`, which carries the 148 credit and reduction slices and runs on port 8080 | root repository |

Next step: `python3 scripts/next_feature_number.py` in that worktree, then `$speckit-specify`
with the number, feeding this document and
[docs/features/payment_matching.md](../features/payment_matching.md) as input.

## Non-goals of this idea

Accelerated time, backdated timestamps, a general bank-statement importer, provider API
emulation, refunds and disputes in the first stages, automatic write-offs or discount
acceptance, dunning letters, and any change to how real connectors record money.
