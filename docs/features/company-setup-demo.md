# Company Setup and Demo Data

The [Demo Data Catalog](demo-data-catalog.md) is the business-facing guide to every
seeded order, purchase, return, credit, payment, inventory and contribution example.

**Status: implemented and verified locally on 2026-09-09.** [Spec 146](../../specs/146-company-setup-demo/spec.md) has a concrete [plan](../../specs/146-company-setup-demo/plan.md), [schema proof](../../specs/146-company-setup-demo/data-model.md) and [review gate](../../specs/146-company-setup-demo/review.md). The routes below are present in the working tree. Release evidence is tracked in the quickstart.

## User contract

Manual first and later company creation share an editable name, Empty/With demo data and ordinary/Sandbox meaning. Empty is default; demo means Sandbox. Previously entered access-application company name is a first-setup suggestion, never a tenant or a rename command. Current admission/membership restrictions remain authoritative; pending owners use their private Playground cockpit.

The canonical international-v12 profile contains 18 items, 20 customers, 3 suppliers, 2 locations, twenty-one operational sales cases, nine purchase cases and 84 days of historical evidence in two comparable 42-day windows. Beyond the standard order, return and settlement journeys it includes a price-only allowance, an exact invoice reversal, partial invoices, final underdelivery, warehouse transfer, damage/loss/scrap, lot expiry, serial receipt, exchange/replacement, prepayment, manual dunning with a stated fee, partial bad debt, customer and supplier deposit clearing, and controlled overdelivery. Every seeded customer and supplier invoice whose timing or discount is demonstrated is bound to the authored `DEMO-14-2` payment term (14 days net, 2% within 7 days).

Its bounded costing portfolio gives every positive-stock item explicit positive acquisition evidence and declares every contribution line that must be current before setup may report Ready. Fixture A derives 40 remaining pcs valued at EUR 420 and 60 billed/fulfilled pcs cost-matched at EUR 630; EUR 1,200 net revenue yields DB1 of EUR 570 and EUR 90 direct plus EUR 24 allocated selling costs yield DB2 of EUR 456 (38%). Five additional exact cases cover healthy, low positive, negative, explicitly zero selling-cost and allocation-heavy DB2 outcomes, plus the late-cost/customer-return trade. Setup records the exact event cutoff, expected/current inventory and contribution counts and at most 20 opaque diagnostics in `PlaygroundRun.initialization_progress.cost_readiness`. These are read-time observations, never stored as authority. Every payment, reversal, costing and commercial-edge decision goes through the same application services a person uses under the profile's narrow initialization authority. Continuous synthetic orders do not invent cost authority or invalidate unrelated reviews; a relevant movement or selling-cost revision is shown as stale until an owner explicitly reviews the new evidence.

Demo Data is an optional synthetic integration, stopped on manual connection, with an average of 10/60/300 orders/hour (default 60); each scheduled delivery carries a Poisson-distributed number of orders (at most six) whose expectation follows a fixed UTC hour-of-day curve (`integrations.demo_data.HOURLY_DEMAND`, 0.7 to 1.3, daily mean 1), decided from the run seed and delivery time, so intake looks like real e-commerce demand: a quiet night, an evening peak and natural minute-to-minute noise. It uses the [implemented shared scheduler/worker](scheduled-jobs.md), normal lossless source intake and interpretation. No browser clock, second queue, provider credentials or automatic stock/reservation/shipment effects. Since [feature 168](../../specs/168-demo-order-to-cash/spec.md) a second schedule issues each order's invoice and records its customer payments through the shared [payment intake core](payment_matching.md); see the order-to-cash section below. Pause/stop retain evidence and resume without a missed-interval burst.

## Free trial entry (Spec 190)

Ordinary web signup explicitly requests a private demo company with live sample data. After email verification and admission, the empty Home entry offers two starts — a demo company with live orders, or an empty company — and calls the confirmed account service `free_playground.enter` with the chosen one; nothing is created until a start is chosen (spec 198). Historical accounts and invitations have no inferred request; existing company links are not redirected. The public offer says “Try for free”, with no initial expiration date and no permanent-free promise, no card and no automatic paid subscription.

`GET /api/company-setup/playground` is read-only. The matching confirmed POST reuses the owner request key `free-playground:v1` for either start, so the receipt records which one was taken, a retry replays the same company and the other start is refused by the existing choice fingerprint. The demo start uses the canonical international profile with live simulation and the existing live setup completion marker; the empty start creates an empty Sandbox in which Demo Data can be connected later. Initialization failure retries the same receipt. Archive is not undone; replay never restarts a paused/stopped completed connection. Practice creation and Storylines are regular product capabilities without a deployment switch (spec 193). Existing account, ownership, confirmation and capacity rules remain authoritative. Legacy enablement settings are ignored.

The three Home starter questions open existing attention, open customer commitments and receivables readers. A voluntary GitHub invitation follows an actually rendered result (delivery detail for the delivery question), never a click, failed read or uninitialized projection. Dismissal is an optional browser preference scoped to the account. No GitHub action or new tracking provider is automatic.

## Implementation entrypoints

Read [company API/UI](../../specs/146-company-setup-demo/contracts/company-setup.md), [profile](../../specs/146-company-setup-demo/contracts/demo-profile.md), [integration](../../specs/146-company-setup-demo/contracts/demo-data.md) and [tests/tasks](../../specs/146-company-setup-demo/tasks.md) before changes. The queued-cancellation extension is implemented in `services/scheduled_jobs.py`; generic pause still preserves pending work. Existing compact lessons remain separate from this canonical profile.

Status and completion evidence belong in [quickstart](../../specs/146-company-setup-demo/quickstart.md). Live deployment requires a separate rollout; creating the specification or schema never activates a connection.

## Reuse from application code

- `services/company_setup.py`: `options`, `create_company`, `read_request`, `retry_request`, `profile`, `create_execution`. Resolve the authenticated account first; retain one request key and identical choices across retries. The first committed Sandbox receipt includes its immutable intent, so explicit replay can recover an interrupted initializer. Reads never seed.
- `services/demo_profile.py` and `demo/international.py`: the versioned canonical baseline. Initialize only through the company orchestrator; never invoke the private seed authority from adapters.
- `services/demo_data.py`: `preview` → confirmed `connect` → confirmed `control`. These controls own a transaction; stale/error cases roll back atomically. `status`, `imports` and `read_import` are scoped, non-persisting observations. `retry_import` reuses the immutable source.
- `jobs/handlers/demo_data.py`: registered `demo.generate_orders`, version 1. Its owner callback admits verified pending private owners only for eligible practice tenants. The handler enqueues and interprets the deterministic sources one delivery plans (`integrations.demo_data.plan`, zero to six orders) inside the scheduler-owned transaction, checking the backlog bound before each order. It never commits or performs business execution.
- `core.process_import_job_bound`: only the registered synthetic interpreters (order, invoice, payment) are supported in this bound path. Expected validation failures retain an import failure outcome; unexpected errors propagate to roll back the worker transaction. Existing public source APIs keep their committing contract.

Both company setup and Demo Data have thin App/account HTTP adapters. First and later creation use `CompanySetup`/`CompanySetupForm`; the source uses `DemoDataIntegration` both in App and owned Playground. Use the shared source preview instead of installing an inert connector shell for `demo_data`.

Empty-company connection preview lists four products, the demo customer pool (`demo/international.py::DEMO_DATA_CUSTOMERS`, the twenty profile customers), Rotterdam Warehouse and the company party required as the outgoing commitment's counterparty. A populated Sandbox reuses existing pool customers and adds the missing ones; Start also adds customers that joined the pool after the connection was made, because intake itself may never create master data. Orders spread over the pool with demand skewed toward its first entries. No supplier, opening stock, historical invoice or reservation is added. Full baseline and ongoing source namespaces remain `demo_profile` and `demo_data` respectively.

Deploy the API, scheduler and worker from the same core revision and apply migration `0046_company_setup_demo` once. See [Worker deployment](../WORKER_DEPLOYMENT.md). No new timer, broker, cron container or provider credential is required. Browser refresh only reads source status; it is not the source's clock.

## Live company creation

The shared creation request accepts optional strict `live_simulation` (default false), valid only with `international_demo` in a Sandbox. Selecting it and confirming company creation automatically connects Demo Data and starts 60 orders/hour. The owner does not need to configure or start the integration separately. Static demos and later manual connections remain available. No real external integration is automatically authorized.

The flag is immutable creation intent in the existing PlaygroundRun JSON and part of its request fingerprint. After baseline seeding, shared connection/start services and `live_setup_complete` commit atomically. Failed setup retains the same baseline and exposes a retryable, non-ready result; GET never performs setup. A completed request remains completed even if the owner later pauses/stops the source. No new schema or scheduler mechanism.

Spec 146 FR-023: first and later creation use one goal-based choice: Start your own company, Create an empty Sandbox, or Try demo data. Only the demo choice shows optional Enable live simulation. Selecting demo defaults it on; the owner may turn it off, and switching away clears it. Eligibility filters available choices. The existing environment/content/live_simulation API contract is unchanged.

Spec 146 FR-024: name is visibly required with helper text. Create remains actionable when the name is missing; empty/whitespace submissions show a localized inline alert and focus/scroll the invalid name field without a request. Correction clears the message and startup/live choices remain intact.

Spec 146 FR-025 supersedes the post-creation ready/profile/action menu: a ready result automatically enters the new company and shows a dismissible creation confirmation there. A recovered ready receipt also opens automatically. Opening failures preserve the request and expose a retry without a new creation/start action. Integration management stays in Integrations.

FR-026–028: the shell labels Sandbox beside the company name. Reports and contributor reads accept authorized practice tenants without changing mutation or admission policy. Demo Data presents state-aware primary controls and a latest-25 activity widget; five-second visible-page refresh only reads data. Recent snapshots use `imports?recent=true`, ordered by persisted import `created_at DESC, id DESC`; `has_more` labels truncation and no cursor is returned. Default history cursor behavior is preserved. Entries expose actual creation/completion times and held document numbers; next arrival is a scheduled time, not a guaranteed execution. Failed refresh retains existing data with a stale warning, and polling preserves input/confirmation state.

FR-029 moves the controls/live widget to `/app/demo-data?tenant=…`, reached by Demo Data immediately below Companies in the Company group for demo-profile companies or those with a Demo Data connection state. Integrations no longer embeds this panel. The dedicated route preserves service eligibility and tenant scope. This supersedes earlier descriptions placing the widget inside Integrations.

Sandbox Exceptions investigation (FR-030) uses scoped tenant existence reads in
`services/attention_reads.py`; do not reintroduce the ordinary-workspace mutation
guard for this read-only register or finding detail. Existing API company admission,
canonical exception derivation and action restrictions continue to apply.

Spec155 business read parity: Warehouse registers, master-data registers/details,
master-data proposal inspection, source metadata, existing item-import previews
and original CSV downloads use tenant existence and scoped records, without
ordinary-company mutation guards. Authentication, owner/readiness checks, temporary
lesson boundaries and existing write/credential policies remain unchanged.

## Order-to-cash stream (feature 168)

- `integrations/demo_data.py::settlement_plan` derives one reproducible story per order from the order schedule's seed: money path (60 % provider capture, 40 % bank transfer), outcome (91 % exact, 4 % short, 1 % over, 1 % unmatched, 2 % late, 1 % never), compressed wall-clock delays, stated amounts and the typed references the payer writes. `produce_invoice` and `produce_payment` build lossless payloads; `normalise_invoice`/`normalise_payment` hand them to `services/payment_intake.py`.
- `jobs/handlers/demo_data.py::SETTLE` (`demo.settle_orders`, version 1, every 60 seconds) calls `services/demo_data.py::settlement_work`, which scans the connection's orders of the last 30 days that can still owe a record, recomputes their plans and emits at most 25 due invoices or payments per occurrence, oldest first, under `settlement_scope`. Identities are `{order external id}:invoice` and `{order external id}:payment:{n}`; existing records are the only idempotency marker.
- Connect creates or matches the payment term `DEMO-14-2` (14 days net, 2 % within 7 days). Start creates both schedules; pause, stop and disconnect cancel both; `set_rate` changes only the order schedule; saturation counts every synthetic type. A connection created before this feature receives its settlement schedule on its next start. Migration `0055_demo_settlement_schedule` adds the nullable `settlement_schedule_id`.
- `status` carries `order_to_cash`: invoices issued, payments received and allocated, invoices settled, open residuals, customer credit created, unmatched payments, failures, last and next settlement, computed from source records and read services. The integration panel shows the block with links into Payments, Open items and Journal.
- The settlement authority (`tenant_policy._SETTLEMENT_OPERATIONS`) may post the stated invoice, record payments and allocate an unambiguously stated reference; it may not reduce, refund, write off or reserve. The order scope keeps its narrower set, so an order can never book money.

## Initialization outside the request (feature 199)

Creating a company with profile content commits the tenant, membership and run metadata
and then enqueues `company_setup.initialize` (version 1, configuration `{run_id}`)
through `services/scheduled_jobs.py::create_manual_run`, keyed `setup-initialize:{run id}`
so a repeated request replays the queued run instead of adding a second. The request
answers with the receipt, which reports `initializing`; the seed no longer travels with
it. The measurement that justified this: one seeding request issued 6,447 SQL
round-trips, 3.2 s against a loopback database and proportionally more over a network,
which is what made `Failed to fetch` on the preparing screen intermittent.

`jobs/handlers/company_setup.py::INITIALIZE` runs `initialize_profile` and
`_finish_live_setup` in their transaction-bound form, so handler writes and run success
commit together and an already active run is a no-op. Authorization resolves the
playground run's own owner at enqueue and again at claim, because a verified account
pending admission may create a Sandbox; `scheduled_jobs._owner` routes the job type,
and `create_manual_run` now authorizes by job type exactly as a schedule does.

A company that seeds no profile, a failed initialization and the explicit retry are all
completed inside the request, so a company is recoverable where no worker is running.
The preparing screens follow the receipt (`unified/setupProgress.ts`): the first read is
immediate and the rest run every second, for at most three minutes, after which the
existing retry is offered. The receipt reports `preparation` — `queued` while the seeding
run waits, `preparing` once a worker has claimed it, `null` otherwise — and the screens
render three steps from it (feature 201). Nothing about that display is estimated: the
middle step only claims work is happening once a worker actually holds the run.

FR-033 supersedes that three-step count for canonical demo setup. The setup worker uses
the shared projection service to publish the initial operational projections after the
profile and requested live source are prepared, in the same retryable transaction. The
screen shows a fourth Finance/margin calculation outcome before Ready to explore and
keeps both the completed calculation and final readiness confirmations visibly readable. A ready
fresh demo therefore has an initial stored Finance answer and does not depend on a manual
Refresh click, browser calculation or browser-owned background work.

Spec146 FR-031: company setup distinguishes busy preparation/opening from recoverable interruption. Busy states use one spinner/status and retain the company name without retry actions. First-company entry renders one centered heading/card; existing-company selection remains. Saved request identity and automatic ready navigation are unchanged.

## Existing Sandbox simulation entry

Owner Sandbox/demo cards link to the existing company-scoped Demo Data controls (FR-032). Opening the page performs no mutation. Backend eligibility remains authoritative. Unsupported practice companies offer a separate demo through normal confirmed setup; demo/live choices are initially selected only when setup options allow them. Saved requests override initial suggestions. Historical fixtures and Storyline companies are never reseeded or converted.

FR-032 correction: unsupported simulation entry links to Companies instead of opening an inline demo creation dialog. The hint suggests an empty Sandbox; historical demo data is not required for subsequent simulation. Eligible existing Sandboxes continue to use the existing preview/connect/start controls.

Spec 195 independent Free Play uses the existing confirmed creation service with
request key `standalone-free-play:v1`, `sandbox` / `international_demo`, and no live
simulation. It has no Storyline identity. Reopen and retry preserve the same receipt;
archive is respected. No profile, admission, lesson or scheduling contract changes.

The Free Play chooser also opens existing accessible companies without creating,
seeding or converting them. Its default is the current company; ordinary company
chat preserves normal proposal confirmation and access rules.

## First live orders and header (spec 207)

A fresh confirmed Demo Data Start makes three one-order occurrences due at activation,
12 seconds and 24 seconds. These initial deliveries are deterministic even when normal
random demand would be zero. Subsequent deliveries use the selected rate and existing
hourly demand distribution. Initialization must finish first; scheduler/worker load can
delay actual processing. Existing running schedules are not retroactively accelerated.
Pause/stop and rate changes abandon remaining initial timing; ordinary resume does not
re-arm it. Downtime coalesces missed slots without a burst. Intake, retry identities and
source controls remain unchanged.

The current company's header shows a compact, subtly pulsing Live simulation link only
when the existing authorized status reader reports running without a derived error or
throttle. It opens the existing Demo Data overview. It is absent for all other states,
failed reads and unauthorized companies; company switches discard old responses. Visible
shells refresh every five seconds with bounded cancellation. Reduced motion disables the
pulse; narrow headers retain an accessible compact link outside the overflow menu.
## Production tool boundary (spec 249)

Demo profiles and continuous synthetic intake use the production application tools and
services. They must not register demo-only mutations, write business tables directly, or
bypass proposal review. A mutation proposed through MCP is reviewed and confirmed in Web
through the same tenant-scoped production boundary as a mutation in an ordinary company.

## A live source that stopped (spec 256)

`services.demo_data.status` derives a `stall` beside its counters: the kind
(`suspended`, `stopped`, `unresolved`, `overdue`, `throttled`), the error code, when it
stopped, how many attempts were made, the recovery moment when one is pending, and
whether recovery happens by itself. Nothing of this is stored; it follows from the
schedule and its last occurrence. `overdue` reports an enabled schedule whose next
occurrence has passed by three intervals, never less than two minutes — the state that
shows a scheduler or worker that is not running at all.

Reference compatibility follows the source, not the catalog. A company that already
has a connection resolves its references leniently: an entry the canonical profile
gained after that company was created is simply absent, and the references the running
schedule captured are still compared, so a reference that truly disappeared refuses
with `incompatible_references`. Items are matched by name and unit, never by their
human item number, which changed shape from `P01` to `ITEM-001` while existing
companies kept theirs. A first connection is still established against the full
current catalog.

A connected simulation is operated through its registered source, like any other
system; the separate card on the integrations page appears only while nothing is
connected, because there is no source row to open yet.

Where the simulation is set: the source's own configuration dialog carries the
simulation's state, reason, rate and controls (`DemoDataIntegration` with
`variant="settings"`), because that is the one place a person configures this source.
Its observations — counters, order to cash and live activity — stay on the simulation
page, one step away. The source row in the integrations table states the live state in
a single word and carries the full reason in its title.
