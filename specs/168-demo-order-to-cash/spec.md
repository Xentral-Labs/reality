# Feature Specification: Demo Data pays its orders

**Feature Branch**: `168-demo-order-to-cash`
**Created**: 2026-09-10
**Status**: Draft
**Language**: English
**Input**: "Demo Data also emits synthetic invoices and customer payments that Reality records, deterministically allocates and, where ambiguous, proposes for confirmation. Most payments are exact; some are short, over, late, unmatched or missing, at roughly the frequency of real e-commerce. Payments must take the same internal path a Stripe or PayPal integration will take later."

## Context and Intent

### Problem

Demo Data (spec 146) creates one synthetic sales order per scheduled occurrence and stops.
Its contract forbids anything else: "Source activity never reserves, fulfills, ships, pays or
replenishes" (FR-018, SC-009). A running demo company therefore shows a growing order list
while Open Items, Payments, the Journal and the customer credit view stay frozen at the
seeded 84-day baseline. The part of Reality that is hardest to fake, money arriving against
invoices with every difference explainable down to the bank line, is never shown, and the
finance work of spec 148 (available credit, accepted reductions) has nothing continuous to
act on.

Independently, Reality has no payment intake path at all. Payments are recorded on explicit
human command or through the bank-statement CSV profile, which records money and never
allocates it. No provider interpreter exists; the connector catalog declares empty shells for
Stripe, Shopify Payments and PayPal. Whatever Demo Data does with payments becomes the first
payment intake in the product, so it must be the path real providers will take, not a demo
shortcut.

The owner took seven decisions on 2026-09-10; they are recorded in
[docs/ideas/demo-order-to-cash.md](../../docs/ideas/demo-order-to-cash.md) and are binding
input here.

### Scope

- Two new synthetic record types from the existing `demo_data` source: an invoice for each
  synthetic order and one or more customer payments for that invoice, produced
  deterministically from the run seed with a fixed, tabled outcome mix.
- A shared, provider-agnostic payment and invoice interpretation core in a new service
  module, with thin per-source normalisers; Demo Data ships the first normalisers.
- Three-tier matching: record always; allocate only references the source states and that
  resolve to exactly one posted invoice; otherwise compute read-time candidates that a person
  or agent confirms through the existing proposal tools.
- A second durable schedule that emits due invoices and payments in bounded batches,
  controlled by the existing Demo Data controls.
- A narrow intake authority that lets the synthetic source post the invoice it states and
  allocate unambiguous payments; amendment of spec 146 FR-018 and SC-009 accordingly.
- Demo Data status and integration panel extended with order-to-cash counts; Payments and
  Open Items show candidates and differences through existing views.
- A payment term with a discount window created or matched on connect, so discount
  explanations can fire.

### Non-Goals

- Accelerated time or backdated business timestamps; delays are compressed wall-clock.
- Fuzzy or probabilistic allocation, amount tolerances, automatic write-offs, automatic
  discount acceptance, automatic refunds, dunning.
- Provider money paths (provider clearing, fees, payouts, bank confirmation of payouts);
  payments post to the tenant's default cash account until spec 148 money paths exist.
- A webhook endpoint, signature verification, SKU or customer mapping; the synthetic source
  carries internal identities and enters through the scheduler like today.
- Supplier payments, refunds, credit notes, returns and disputes in the synthetic stream.
- Real Stripe, PayPal or Shopify Payments normalisers; the core is built for them, they are
  separate features.
- Any change to how existing public intake APIs commit, or to the committing behaviour of
  invoice-bound `post_customer_payment`.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md), [workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md).
- [Company setup and Demo Data](../../docs/features/company-setup-demo.md), spec 146 and its
  [demo-data contract](../146-company-setup-demo/contracts/demo-data.md), which this feature
  amends.
- [Scheduled jobs](../../docs/features/scheduled-jobs.md), spec 147.
- [Ledger](../../docs/features/ledger.md), [order to cash](../../docs/features/order_to_cash.md),
  [source ingestion](../../docs/features/source_ingestion.md).
- Proposed [payment intake and matching contract](../../docs/features/payment_matching.md),
  which this feature delivers for the customer side.
- Spec 076 (invoice lines bill order lines), 088 (early-payment discount, no rate arithmetic in
  services), 091 (invoices are booked), 148 (account catalog, payment differences: available
  credit and accepted reductions, present in this checkout).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An order is invoiced and paid exactly (Priority: P1)

A demo owner starts Demo Data. Minutes after an order arrives, an invoice for it appears and
is booked; minutes later a payment arrives, is recorded and allocated, and the invoice shows
as paid. Open Items, Payments and the Journal move without anyone touching them.

**Why this priority**: This is the smallest slice that makes the finance views live and proves
the shared path end to end. Every other story adds a variation of the payment.

**Independent Test**: Run one order through the settlement schedule with a seed whose plan is
"exact, bank transfer" and verify through public read services that one booked invoice bills
every order line, one payment is recorded against the source record, one allocation settles
the invoice, and the open items view shows it paid.

**Acceptance Scenarios**:

1. **Given** a running Demo Data connection with a synthetic order older than its planned
   invoice delay, **When** the settlement occurrence runs, **Then** exactly one `invoice`
   SourceRecord with identity `{order external id}:invoice` exists, a `sales_invoice` document
   references it, every invoice line carries `billed_document_line_id` to an order line, and
   the invoice is posted with balanced receivable and revenue entries.
2. **Given** that booked invoice and a payment plan "exact" whose due time has passed,
   **When** the occurrence runs, **Then** one `payment` SourceRecord `{order external id}:payment:1`
   exists, a `customer_payment` document and a cash/receivable posting reference it, one
   settlement allocation equals the invoice total, and `open_invoice_amount` is zero.
3. **Given** the same occurrence is retried after a rollback, **When** it runs again, **Then**
   the stored payloads are reused, no second document, posting or allocation is created, and the
   interpretation outcome is `interpreted` once.
4. **Given** the invoice interpretation fails validation, **When** the occurrence completes,
   **Then** the source is retained with a `failed` outcome, no business record from that
   interpretation persists, and the scheduler occurrence completes.

---

### User Story 2 - Short and over payments stay honest (Priority: P1)

Some customers pay less (they deducted a discount, withheld freight, paid part) and a few pay
more (paid twice, typed a rounded figure). Reality allocates what it can, shows the exact
difference, and leaves the decision about the difference to a person.

**Why this priority**: Differences are what the owner wants to demonstrate, and the demo must
prove that Reality never hides or forges a settlement.

**Independent Test**: Run seeds whose plans are "short: discount", "short: withheld",
"short: partial then rest", "over: duplicate" and "over: typo" and verify open amounts,
available credit and raised exceptions through public reads.

**Acceptance Scenarios**:

1. **Given** an invoice of 1,000 open and a stated payment of 980 with the invoice number as
   reference, **When** it is interpreted, **Then** 980 is allocated, 20 remains open, the
   invoice status is partial, no reduction is booked, and if the invoice's payment term
   explains 20 within its discount window the overdue exception later carries the
   `early_payment_discount_taken` tag.
2. **Given** an invoice of 1,000 open and a stated payment of 1,020 with a clean reference,
   **When** it is interpreted, **Then** 1,000 is allocated, the invoice is paid, 20 remains as
   unallocated payment credit visible for the customer, and `unmatched_financial_event` names
   the 20.
3. **Given** a partial plan, **When** the second payment arrives later with the same
   reference, **Then** it is allocated up to the remaining open amount and the invoice becomes
   paid without a second cash entry for the first payment.
4. **Given** a duplicate plan, **When** the second identical payment arrives, **Then** it is
   recorded as a separate payment with its own source identity, nothing is allocated because the
   invoice is already paid, and the full amount remains as customer credit.
5. **Given** any short payment, **When** the owner opens Open Items, **Then** the row shows
   paid amount and remaining claim separately and offers the spec 148 actions leave open,
   explain a deduction, accept a stated reduction; none of them has run automatically.

---

### User Story 3 - A payment without a usable reference is proposed, not guessed (Priority: P2)

A bank line arrives with only the customer number, with the customer's own purchase-order
number, or with a typo in the invoice number. Reality records the money, allocates nothing,
and shows the likely invoices with the reason each one fits. The owner, or an agent through
MCP, confirms one.

**Why this priority**: This is the case where a wrong automatic choice would be worse than
none, and where the human or agent step of the product becomes visible.

**Independent Test**: Run "unmatched" plans and verify that the payment is recorded and
unallocated, that candidates are returned by the read service with reasons, that they are not
persisted, and that confirming one through the proposal tools allocates within bounds.

**Acceptance Scenarios**:

1. **Given** a payment whose only reference is the customer number, **When** it is interpreted,
   **Then** it is recorded against the payer, no allocation exists, and the candidate read
   returns the party's open invoices whose open amount equals the payment amount, each with
   the reason "amount equals open amount".
2. **Given** a payment whose reference contains an invoice number with one wrong digit,
   **When** it is interpreted, **Then** nothing is allocated and the candidate read returns
   invoices whose number appears as a substring, or none, with the reason stated.
3. **Given** a stated shop order that is billed by two invoices, **When** the payment is
   interpreted, **Then** nothing is allocated and both invoices are candidates with the reason
   "order billed by more than one invoice".
4. **Given** candidates, **When** the owner or an authorised agent confirms one through the
   existing proposal flow, **Then** `allocate_settlement` runs with the tier-2 bounds, the
   allocation records actor and reason, and reading candidates afterwards returns none for the
   allocated amount.
5. **Given** candidates were read twice without any change, **When** the results are compared,
   **Then** they are identical and no table row was written by either read.

---

### User Story 4 - The owner controls and observes the money stream (Priority: P2)

The Demo Data panel shows how many invoices and payments arrived, how many settled, how many
differences and unmatched payments exist, and when the next settlement runs. Pause, resume,
stop and disconnect apply to orders and settlements together; the rate control keeps affecting
orders only.

**Why this priority**: Without observability the owner cannot trust the stream, and without
shared controls a paused demo would keep paying.

**Independent Test**: Exercise every control action against a connection with both schedules
and verify schedule states and status counts through the service and the HTTP adapters.

**Acceptance Scenarios**:

1. **Given** a stopped connection, **When** the owner starts it, **Then** an order schedule at
   the chosen rate and a settlement schedule at a fixed 60-second interval exist and the
   connection references both.
2. **Given** a running connection, **When** the owner pauses, stops or disconnects, **Then**
   queued work of both schedules is cancelled and neither produces records until resume or
   start; **When** the owner changes the rate, **Then** only the order schedule changes.
3. **Given** twenty pending or failed synthetic imports of any type, **When** either occurrence
   runs, **Then** the connection pauses visibly and both schedules stop producing.
4. **Given** a paused period longer than several payment delays, **When** the owner resumes,
   **Then** due settlements are emitted at most 25 per occurrence, oldest first, with no
   burst beyond that bound.
5. **Given** the App or owned Playground status route, **When** read, **Then** it reports
   invoices issued, payments received, allocated, settled invoices, open residuals, customer
   credit created, unmatched payments and last settlement time as counts over source records
   and read services, never from a stored counter.

---

### User Story 5 - Late and never-paid invoices age (Priority: P3)

A few customers pay after the due date and about one in a hundred never pays within the demo.
The aging register shows them, the overdue exception names them, and nothing changes the
claim.

**Why this priority**: It completes the realistic picture but is only visible on demos that run
longer than the fourteen-day term.

**Independent Test**: Run "late" and "never" plans with an as-of date beyond the due date and
verify aging and exception output; verify no payment record exists for "never".

**Acceptance Scenarios**:

1. **Given** a "never" plan, **When** any number of occurrences run, **Then** no payment source
   record for that order ever exists and after the due date the invoice appears in the aging
   register and `overdue_receivable`.
2. **Given** a "late" plan, **When** the due date has passed and the planned late time is
   reached, **Then** the payment is recorded and allocated like an exact payment and the
   overdue exception clears because the balance is settled.

---

### Edge Cases

- Tenant boundary: every lookup (invoice by number, order by shop id or number, party by
  customer number) is scoped to the tenant and the payer party; a matching number in another
  tenant or another party never resolves.
- Currency: a USD payment never allocates to an EUR invoice; it is recorded and, if a reference
  resolves to an invoice of another currency, becomes a candidate with the reason stated.
- Account mismatch: the payment is pinned to the invoice's own receivable control account;
  if that account is blocked, the payment is still recorded to an allowed account and no
  allocation is attempted.
- Unposted invoice: a payment whose reference resolves to an invoice that is not yet posted is
  recorded and unallocated; it becomes allocatable only through a later confirmation.
- Payment before invoice: the settlement plan orders the invoice before every payment; if the
  invoice occurrence failed, the payment is still recorded and waits as credit.
- Replay and retry: same source identity, same stored payload, no new timestamp; a payment
  retry after a failed allocation does not record cash twice.
- Reference resolves to a reversed invoice: treated as not resolving.
- Empty references: recorded, no candidates unless an amount match exists.
- Connection references changed since the schedule was created: both occurrences refuse with
  `incompatible_references` like today.
- Owner loses eligibility, archives or disconnects: both schedules stop; nothing already
  recorded is removed.
- Payment term missing or blocked reduction account: connect creates or matches the term;
  a missing reduction account only prevents later human reductions, never recording.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `demo_data` source MUST declare two additional capabilities, `invoice` to
  `sales_invoice` and `payment` to `payment`, without credentials or provider claims, and its
  catalog text MUST describe orders, invoices and customer payments.
- **FR-002**: A pure planning function MUST derive, from seed, schedule id and delivery id, the
  money path, outcome, delays, stated amounts and stated references of an order's invoice and
  payments; the same inputs MUST always yield the same plan.
- **FR-003**: The version 1 outcome table MUST be, per order: exact and on time 91 %, short
  with claimed discount 2 %, short with a withheld small amount 1 %, short partial with a later
  rest payment 1 %, over by duplicate or typo 1 %, unmatched reference 1 %, late but paid 2 %,
  never paid 1 %; money path provider capture 60 % and bank transfer 40 %; differences MUST
  occur only on the bank-transfer path. The table MUST live in one place in the producer.
- **FR-004**: Short and over amounts MUST be stated as facts in the payment payload; no service
  MUST compute them from a rate or the invoice amount.
- **FR-005**: The synthetic order payload MUST carry a shop id, a readable order number and a
  customer reference as separate values; the invoice payload MUST carry the order identity,
  invoice number, issue date, due date, payment term code, currency, source-stated amounts and
  lines naming the order line they bill; the payment payload MUST carry money path, amount,
  currency, effective time, payer, the typed references the payer or provider states, and the
  payment index.
- **FR-006**: External identities MUST be `{order external id}:invoice` and
  `{order external id}:payment:{n}`, where the order external id is the existing
  `{schedule}:{run}[:{position}]`; retries MUST reuse the stored payload and identity.
- **FR-007**: Invoices MUST state the payment term "14 days net, 2 % discount within 7 days";
  connect MUST create or match that term as a demo prerequisite.
- **FR-008**: Delays MUST be compressed wall-clock: invoice 2–10 minutes after the order,
  provider capture 1–3 minutes after the invoice, bank transfer 10–90 minutes after the
  invoice, second payments 20–120 minutes after the first, late payments after the due date.
  Business timestamps MUST be the occurrence time, never backdated.
- **FR-009**: A shared invoice interpretation core MUST create the `sales_invoice` document
  with lines linked to order lines and post it, and MUST return the existing document on
  replay.
- **FR-010**: A shared payment interpretation core MUST record every payment as a
  `customer_payment` document with a cash/receivable posting linked to its source record,
  before and independently of any allocation.
- **FR-011**: The payment core MUST allocate automatically only when a stated reference
  resolves, within the tenant, payer party and currency, to exactly one posted, non-reversed
  invoice; the allocated amount MUST be the lesser of the payment's unallocated amount and the
  invoice's open amount; the payment MUST be pinned to that invoice's receivable control
  account.
- **FR-012**: Stated references MUST resolve by type: invoice number to the party's posted
  invoices; shop id to the order source record's external id in the matching source system,
  then through billed lines to the invoice; shop order number and customer reference to the
  party's orders, then to the invoice; customer number to the party only.
- **FR-013**: The payment core MUST never over-allocate, write off a residual, accept a
  discount, create a credit note or refund, or create an invoice for a payment.
- **FR-014**: A read service MUST compute candidates for an unallocated payment: same party
  and currency with open amount equal to the unallocated amount; invoice number as a substring
  of the remittance text; a stated reference resolving to more than one invoice. Each
  candidate MUST carry its reason. Candidates MUST NOT be persisted.
- **FR-015**: Confirming a candidate MUST run through the existing proposal creation and
  execution flow and call `allocate_settlement` with the FR-011 bounds; MCP and Chat MUST reach
  the same candidates and the same confirmation.
- **FR-016**: The core and normalised shapes MUST live in a new service module
  (`services/payment_intake.py`); Demo Data normalisers MUST map the synthetic payload one to
  one and reject unknown schema versions or a missing synthetic marker.
- **FR-017**: `("demo_data", "invoice")` and `("demo_data", "payment")` MUST be registered
  interpreters; the bound processing path MUST accept all three synthetic types with the same
  savepoint semantics.
- **FR-018**: A second job definition `demo.settle_orders` MUST run every 60 seconds, select
  the connection's orders whose planned invoice or payment is due and has no source record
  yet, and emit at most 25 records per occurrence, oldest due first, through the normal
  intake.
- **FR-019**: The connection MUST reference its settlement schedule; start MUST create both
  schedules; pause, stop and disconnect MUST cancel queued work of both; resume MUST resume
  both; `set_rate` MUST leave the settlement schedule unchanged; stop and start MUST create a
  new settlement schedule id.
- **FR-020**: The saturation rule of twenty pending or failed synthetic imports MUST count all
  three types and pause both schedules.
- **FR-021**: A narrow intake authority MUST allow the settlement job to post the stated
  invoice, record payments and allocate FR-011 matches, and nothing else; it MUST be bound to
  the synthetic source and the practice tenant like the existing intake scope.
- **FR-022**: Spec 146 FR-018, SC-009 and the demo-data contract MUST be amended to state that
  synthetic activity may issue invoices and record and allocate payments under FR-021, and
  still never reserves, fulfills, ships or replenishes.
- **FR-023**: Demo Data status MUST report invoices issued, payments received, allocated
  amount, settled invoices, open residuals, customer credit created, unmatched payments and
  last settlement time, computed from source records and read services.
- **FR-024**: The Demo Data integration panel in App and owned Playground MUST show those
  counts with links to Payments, Open Items and the Journal, localised in the four languages.
- **FR-025**: Existing exception classes MUST surface the differences without new rules:
  `unmatched_financial_event` for unallocated remainders, `overdue_receivable` for late and
  never-paid invoices, the discount tag where the term explains a short payment.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality is preserved for every synthetic record: SourceRecord
  → ImportJob → interpretation → Document and DocumentLine → LedgerEntry and
  SettlementAllocation. The producer writes no business record.
- **DR-002**: Shortest true links only: invoice lines to order lines, allocations between two
  ledger entries, payments to their source record. Human numbers are looked up and never
  stored as links; the remittance text is retained verbatim in the payload.
- **DR-003**: Paid, partial, open, overdue and available credit remain read-time derivations;
  candidates are read-time observations; no new balance, status or candidate table exists.
- **DR-004**: Every new query and the settlement job are tenant-scoped and owner-authorised on
  each occurrence exactly like the order job; the new column is tenant-scoped through the
  connection.
- **DR-005**: The single schema change is one nullable `settlement_schedule_id` on the Demo
  Data connection, justified by FR-019; the migration is reversible.
- **DR-006**: Producer (`integrations/`) and consumer (`services/`) share no parsing code; only
  the consumer is shared between Demo Data and future provider normalisers.
- **DR-007**: No service multiplies a gross amount by a discount rate (spec 088 DR-007); stated
  amounts come from the payload.

### Key Entities *(when data is involved)*

- **Synthetic invoice record**: lossless billing evidence for one synthetic order; becomes a
  posted sales invoice whose lines bill the order lines.
- **Synthetic payment record**: lossless bank line or provider capture; becomes a recorded
  payment and, when unambiguous, an allocation.
- **Normalised payment / normalised invoice**: the provider-agnostic shape the shared core acts
  on; carries only fields the core uses plus the list of typed references.
- **Settlement schedule**: the second durable schedule of a Demo Data connection.
- **Candidate**: a read-time pairing of an unallocated payment and an invoice with a reason;
  never stored.

## Success Criteria *(mandatory)*

- **SC-001**: On a fresh practice company with Demo Data at 60 orders per hour, Open Items,
  Payments and the Journal show new settled invoices within 15 minutes of start without any
  manual action.
- **SC-002**: Over 10,000 seeded plans the outcome shares are within one percentage point of
  the FR-003 table, and every difference lies on the bank-transfer path.
- **SC-003**: No automatic allocation ever exceeds an invoice's open amount or a payment's
  unallocated amount; no automatic action ever reduces a receivable other than by allocated
  cash.
- **SC-004**: Every unmatched synthetic payment appears in Payments with candidates or with an
  explicit "no candidate" state, and confirming a candidate settles it with the same result a
  manual payment posting would give.
- **SC-005**: Pause, stop and disconnect stop both streams within one occurrence; resume never
  emits more than 25 settlement records per occurrence.
- **SC-006**: A later provider normaliser can be added by registering one interpreter and
  adding mapping tests only; the core's behaviour tests are unchanged.
- **SC-007**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The owner's seven decisions of 2026-09-10 hold: 14-day terms with discount window, second
  schedule with one column, narrow automation authority, synthetic invoice evidence, weight
  table version 1, new service module, this checkout as base.
- The spec 148 account catalog and the available-credit and accepted-reduction slices present
  in this checkout (migrations 0048 and 0049) remain; payments post to the default cash
  account until money paths exist.
- Practice companies receive the five reference accounts on creation; connect only verifies
  them.
- The shared scheduler (spec 147) supports a second schedule per connection and the existing
  `cancel_queued_run` extension.
- Overdue behaviour is visible only on demos running longer than fourteen days, such as the
  Railway demo; this is accepted.
- The existing bank-statement CSV profile keeps its behaviour; adopting the shared core for it
  is a later, separate change.
- The docs-site guide drafts in `docs/ideas/payment-matching-guide/` move to the docs site only
  when this feature ships.
- The settlement schedule scans synthetic orders of the last 30 days only; every planned
  invoice and payment, including late ones, falls inside that window, and an order that never
  pays simply leaves the scan after 30 days.
- A connection created before this feature receives its settlement schedule on the owner's
  next explicit start; nothing is created for it by the migration.

## Open Questions

None. All owner decisions are recorded; technical placement questions belong to the plan.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US4 scenario 1 | connector catalog and source capability tests |
| FR-002, FR-003, FR-004 | US2 all, SC-002 | unit tests of the planner: determinism, distribution over 10,000 seeds, stated amounts |
| FR-005, FR-006 | US1 scenarios 1–3 | payload schema tests, identity and replay tests |
| FR-007 | US2 scenario 1, edge case term | connect prerequisite test, discount tag test |
| FR-008 | US1, US5 | planner delay ordering tests |
| FR-009 | US1 scenario 1, 3, 4 | invoice core service tests |
| FR-010, FR-011, FR-012, FR-013 | US1 scenario 2, US2 all, US3 scenarios 1–3, edge cases | payment core service tests fed with normalised evidence |
| FR-014, FR-015 | US3 scenarios 1–5 | candidate read tests, proposal flow tests, MCP tool test |
| FR-016 | SC-006 | module boundary test; normaliser tests |
| FR-017 | US1 scenario 4 | bound processing tests for all three types |
| FR-018, FR-019, FR-020 | US4 scenarios 1–4 | job handler and control tests, migration round trip |
| FR-021, FR-022 | US1, US2 | tenant policy scope tests; spec 146 amendment review |
| FR-023, FR-024 | US4 scenario 5 | status service tests, App and Playground adapter tests, web contract and browser script, localisation audit |
| FR-025 | US2 scenarios 1–2, US5 | exception tests |
| DR-001–DR-007 | all | business-story test order → invoice → payment variants; isolation catalog; migration review |
