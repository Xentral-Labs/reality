# Reactive company simulator

## Live company with an external code agent (spec 376)

Use the [live startup and operating guide](LIVE.md), including its single external-agent prompt, explicit Operational-case readiness/takeover/handback guidance, supplier purchasing prerequisites and automatic restart/full-round acceptance checklist. A completed agent response is not continuous operation; the external host must provide and verify the next wake. This is a retained PostgreSQL company, paced by the existing scheduler/worker, with a simulator-local inbox/outbox and a separate live console. The external Claude/Codex agent uses ordinary Reality tools; no built-in policy acts for it. The default target is 180 new orders/hour for 72 hours (150–200/hour and 96 hours are configurable). These are configured targets; a multi-day throughput trial and an actual external-model trial have not been measured.

The live console offers **Trigger an event → Preview → Release** for customer/supplier mail, new orders, delivery enquiries, cancellations and return requests. Preview creates no records. A released email alone does not book stock, money or an order. Every manual release has its own immutable identity and is counted separately. No real email integration or open desktop is required.

The commands below this section remain **finite regressions and artifact replay**. They do not start this sustained runtime. The old replay Play button controls viewing only.


One finite rehearsal controller, three reviewed profiles. Sources, orders, stock, shipments and financial effects use normal application services/proposals. No core booking rules are reimplemented in the simulator.

## External code-agent quickstart

Use this directory as the entrypoint. A **launcher agent** starts the existing finite scenario and reports its evidence. A **business operator agent** supplies its own decisions through the Python interface below. Running the built-in `prompt` policy tests the baseline; it does not measure the launcher agent's business decisions.

Prerequisites:

- Follow the repository's [local development setup](../../../../README.md#local-development): Python 3.12+, the root `.venv`, installed `reality-core`, local PostgreSQL and applied Alembic migrations.
- Configure `REALITY_DATABASE_URL` for that local database. The controller accepts only PostgreSQL on `localhost`, `127.0.0.1` or `::1`. It does not start PostgreSQL or apply migrations.
- Obtain an existing active, verified, admitted owner's opaque user ID through the normal authenticated account flow. Local `GET /api/auth/me` returns it as `id`. Do not invent an ID or insert an owner directly into the database.
- Use a local test database. Each confirmed launch creates a fresh company and retains its records; launching again is not a resume.

Open two terminals, both in `packages/reality-core`. Start the spectator first:

```sh
../../.venv/bin/python -m scenarios.company_simulator.viewer --root ../../artifacts/company_simulator --port 8765
```

Then replace `OWNER_ID` with the actual owner's ID and start the baseline:

```sh
../../.venv/bin/python -m scenarios.company_simulator.controller --actor-id OWNER_ID --confirm --profile complete --operator prompt --days 30 --output ../../artifacts/company_simulator
```

Open **http://127.0.0.1:8765** and select the new run. The writer's `--output` and viewer's `--root` must point to the same directory. The final console line prints the core status and `report.md` path. Keep that run ID when asking for follow-up checks. On a remote workspace, use its normal port-forwarding facility to reach port 8765; a remote loopback URL is not a public preview.

The separate simulator UI already provides a company timeline plus customer and supplier views. It refreshes every five seconds and displays recorded messages, business activity, delivery goals, case coverage and the latest checkpoint. No Reality product UI startup is needed for watching artifacts. See [viewer usage and display boundaries](viewer/README.md). The complete profile records incoming customer and supplier messages plus built-in simulated agent replies. Custom replies remain explicitly unsent drafts. Shopify/operational retain their existing message coverage; old journals are not backfilled.

## What the external agent should check

Check `report.md`/`report.json` for the result and `checkpoints.jsonl` for the independent observations. The controller checks the core at daily simulation checkpoints; the viewer displays those results rather than performing a new verification.

- **Core correctness:** stock per warehouse, reservations, open commitments, shipments/returns and financial postings/allocations agree with the independent scenario expectations.
- **Business outcome:** uncancelled orders reach the original recipient/address, in the required quantity, by the deadline. A correct core can coexist with a missed delivery goal.
- **Coverage:** report exercised versus planned business-case families and pending goals. An incomplete horizon or an idle operator need not exercise the full script.
- **Execution state:** distinguish a completed report from `awaiting_review`, uncertainty or an unfinished journal. Check the latest observation timestamp; an unfinished viewer entry does not prove that a process is alive.

Exit code zero means the core status passed, not that every delivery goal passed. Preserve the receipts and stop on a discrepancy or uncertain execution; reconcile before retrying. Compare fixed milestone totals only with the matching profile, policy and horizon in the [central protocol](../../../../docs/scenarios/company-simulator-protocol.md).

### Copyable launcher-agent prompt

```text
Read AGENTS.md and packages/reality-core/scenarios/company_simulator/README.md.
Start a local company-simulator baseline and its separate read-only spectator.
Use the existing configured local PostgreSQL and an eligible owner's real ID;
if either is unavailable, report the missing prerequisite instead of inventing it.
Run profile complete, operator prompt, 30 compressed simulation days. Start the
viewer first and use matching artifact directories. Report the run ID, exact
commands, report path and reachable spectator URL or required port forwarding.
Inspect independent checkpoints and the final report. Report core status separately
from delivery goals, exercised/planned case families, pending goals and any
stock/commitment/financial differences. Preserve evidence on failure or uncertainty;
do not blindly restart. Do not claim emails were sent or that a process is alive
solely because the viewer shows an unfinished run. This is a finite baseline,
not a test of your own business decisions or a multi-day background service.
```

### Running for three or four real days

`--days 30` means **30 compressed business days**, not 30 real days. There is currently no real-time pacing, durable resume or unattended three-hour monitoring service. Leaving the viewer open does not keep the simulator operating. A manual follow-up can ask: “Inspect run RUN_ID, latest checkpoint and report; summarize core differences, delivery goals and exercised/planned case families, and state whether process liveness was actually verified.”

A future durable runner needs a separately reviewed design using the [shared scheduling contract](../../../../docs/features/scheduled-jobs.md), persistent progress, idempotent recovery and reconciled uncertain effects. Do not improvise a sleep loop or promise that a chat agent will remain active for several days.

## Run

From `packages/reality-core`, with configured **local PostgreSQL** and an existing active admitted owner:

```sh
../../.venv/bin/python -m scenarios.company_simulator.controller --actor-id OWNER_ID --confirm --days 30
../../.venv/bin/python -m scenarios.company_simulator.controller --actor-id OWNER_ID --confirm --days 30 --operator delayed
../../.venv/bin/python -m scenarios.company_simulator.controller --actor-id OWNER_ID --confirm --days 30 --operator wrong_address
../../.venv/bin/python -m scenarios.company_simulator.controller --actor-id OWNER_ID --confirm --profile shopify --days 30
```

`--profile complete` is default and creates a named **ordinary local test company**: Sandbox permissions do not allow the required outbound-plan operations. It never connects an external provider. `--profile operational` retains the original small Sandbox stock/commitment rehearsal. `--days` accepts 1–30; ordinal days run compressed while application clocks remain real. Short runs report pending goals and missing coverage rather than claiming the full month.

## Find the script and the proof

Watch existing or active runs in the separate local spectator:

```sh
../../.venv/bin/python -m scenarios.company_simulator.viewer
```

Open http://127.0.0.1:8765 for the company timeline, customer/supplier views and last
checkpoint. It reads journals without a database and never changes a run. Actual messages
remain separate from business actions. The complete profile includes local supplier notices and
simulated baseline replies; these are never real email sends. [Viewer details](viewer/README.md).

| File | Purpose |
|---|---|
| `profiles/general_company/complete.yaml` | Central month script: customer demand/amounts/addresses/deadlines, quotes, conditional receipts, payments, returns and stock evidence |
| `profiles/shopify_company/scenario.yaml` | Explicitly synthetic Shopify-shaped requests and provider payout statement amounts |
| `complete_world.py` | Private authored world, conditional reactions, independent quantity/posting expectations and released observations |
| `complete.py` | Ordinal controller, business-goal scoring and finite baseline operators |
| `bridge.py` | Normal proposals, preparation-effect guard, exact approval boundary and receipts |
| `complete_observer.py` | Read-only tenant-scoped stock lineage, ledger/allocation and shipment evidence checks |
| `shopify.py` | Production reviewed Shopify order/refund intake and payout settlement adapter |
| `controller.py` | Local CLI/profile selection; retains small spec373 run |

Each run produces `artifacts/company_simulator/RUN_ID/manifest.json`, `events.jsonl`, `messages.jsonl`, `checkpoints.jsonl`, `world.json`, `report.json` and `report.md`. Complete/Shopify runs also publish atomic `spectator.json` files for the read-only viewer. Manifest includes source/profile hashes, owner and actual setup receipt. Accepted world effects retain exact proposal/tool receipts; order references retain opaque IDs. Tests use temporary PostgreSQL companies rolled back by the test fixtures; CLI runs retain their local test companies through normal application services.

## Company coverage

The extended month covers ten customer orders, two customers, two items, two warehouses and demand-dependent procurement. It includes partial supplier receipts and delays; partial customer dispatch; cancellation of whole/unshipped remaining quantities; preserved recipient/address and package carrier arrival; explicit undeliverable return/reopened commitment and re-dispatch; tracking exception without invented stock return; announced/received customer return linked to the original commitment; count loss and warehouse transfer; sales/supplier invoices; partial/full customer payments; supplier payments; separate credit and partial customer refunds. Synthetic customer emails are held losslessly as local Sources and released messages. They are not mailbox transport.

Daily independent checkpoints compare per-order quantities/amounts/IDs, physical stock by warehouse, reservations, live open obligations and pending returns. Financial checks compare each accepted posting's exact accounts, side, amount and party, balanced posting groups, allocation target/amount and remaining invoice/credit balance and held payment allocation state. One authored customer installment falls beyond the horizon, leaving an explicitly expected open receivable of EUR 20. Provider clearing and bank accounts are separately reconciled in the Shopify profile.

Business goals require the complete uncancelled quantity, original recipient/address and actual package evidence by the scenario deadline. Wrong destination can fail business goals with entirely correct core bookings. Core discrepancies stop the run; execution uncertainty retains receipts without retry. Coverage reports state which planned families were actually exercised by that operator/horizon.

## Live external operator

The Python entrypoint accepts a callable `operator(view)` returning commands. The copied view contains only released requests/messages, known quotes, actual current Reality/financial observations and released return/billing statements. It contains no future customer behavior or private expected balances.

Commands: `reply` with a released incoming `message_id`, exact nonempty `subject` and `body` records an unsent draft (no mail authorization or send); `purchase` with `sku`; `ship` with `request_id`, integer `quantity`, optional exact `address`; `cancel`, `invoice`, `credit` with `request_id`; `supplier_invoice`, `supplier_payment` with `purchase_id`. The operator can call its own LLM/agent service; this repository does not choose or enroll a model provider.

A custom operator requires an exact review callback `review(proposal) -> Principal | None`. The principal must be the launch owner and normal confirmation/membership checks still apply. Without review, the report is `awaiting_review` with the concrete proposal. A boolean or read permission does not approve actions. Each step of a composed dispatch is reviewed separately; accepted steps are retained if the next step awaits review.

For a trusted local Python decision module, the CLI can present each exact proposal interactively:

```sh
../../.venv/bin/python -m scenarios.company_simulator.controller --actor-id OWNER_ID --confirm --operator-module my_policy:decide --days 30
```

This is supervised live operation, not blanket approval of unknown AI decisions. Durable pause/resume after process exit is not implemented; pending/uncertain runs must be reconciled before a new run. The built-in finite policies (`prompt`, `delayed`, `idle`, `wrong_address`) are approved as part of the exact reviewed fixture launch.

`my_policy:decide` is a placeholder for a trusted module you implement and make importable from the core working directory (or a controlled `PYTHONPATH`). Custom modules are supported only by the `complete` profile. The CLI asks for `yes` or `no` for each exact proposal; do not pipe automatic approvals into it. `--confirm` does not approve arbitrary future model decisions.

For a business-agent trial, give the agent this additional instruction:

```text
Implement an importable trusted Python decide(view) -> list[dict] adapter for your
business decisions and use --operator-module MODULE:decide with profile complete.
Use only released observations supplied in view; do not inspect private future
scenario data or expected balances to choose actions. Use the documented command
interface and normal proposal/approval boundary, never direct database writes.
Keep exact proposal review interactive. Report awaiting_review when review is not
available. Judge your performance by delivery goals separately from core correctness.
```

## Troubleshooting

| Symptom | Check |
|---|---|
| Database connection or missing-table error | Local PostgreSQL, `REALITY_DATABASE_URL` and migrations from the root setup guide |
| Owner/admission/confirmation error | Actual eligible owner in the same database and explicit `--confirm`; do not bypass normal checks |
| Run missing from the viewer | Matching `--output`/`--root`, correct working directory, selected run and journal timestamps |
| Port already in use | Start the viewer with `--port 8766` and open that port |
| Custom module import error | Replace the placeholder with an implemented importable module and function |
| Review pending or execution uncertain | Preserve report/receipts and reconcile; process restart does not resume the run |

## Shopify coverage and remaining boundaries

The synthetic Shopify profile uses production reviewed intake for three lossless Shopify-shaped orders and a shop refund. Native refund evidence creates an announcement, not warehouse stock or financial credit. A separate legal credit and physical receipt precede refund settlement. Provider statements arrive independently of operator invoices and state EUR 90 charges, EUR 10 refunds, EUR 4 fees and EUR 76 bank deposits. One EUR 10 charge deliberately names an unknown shop reference, leaving clearing at EUR -10. With the prompt operator, the related last invoice retains EUR 10 open. With the idle operator, known payments/refund remain held and unallocated (EUR 80 incoming, EUR 10 refunded), while the same EUR 76 bank deposits and EUR -10 clearing are independently reconciled. Missing invoices do not prevent already-evidenced customer funds from being recorded; an unknown customer reference remains a distinct unmatched source line. Repeated statement receipt does not duplicate accepted records/postings, though audit sequence may advance.

These are synthetic supported examples, **not authentic Shopify Payments export/API format proof**. Original samples remain necessary for native payout mapping. This models an end-to-end trading-company test month, not every industry's accounting: VAT calculation/filing, payroll, regulatory returns, real external mail/provider transport and an unbounded durable daemon are outside this profile. Gross source amounts remain authoritative; the simulator does not calculate tax or prices for upstream sources.

[Readable central month protocol and fixed prompt milestones](../../../../docs/scenarios/company-simulator-protocol.md).

## Verified results

Complete-v2 correspondence: four new acceptance proofs and Chromium checks against the actual 106-message month pass. Latest full backend execution: **6,433 passed, 10 skipped, 1 failed**; the existing settlement fixture clock race was reproduced and corrected, then all **15 affected demo-intake tests passed**. No clean full rerun after the test-only correction is claimed; full CI remains a merge gate. Background telemetry exporter/logging errors also remain recorded in that full log. See [correspondence verification](../../../../specs/374-company-simulator-complete/review.md).

Earlier simulator/spectator integration: **6,430 passed, 10 skipped**, no failed tests; see [spectator verification](../../../../specs/375-simulator-spectator/review.md). The earlier expanded-profile backend verification was 6,391 passed / 10 skipped. Independent final-month milestone proof and financial/privacy/exact-review acceptance passed. Detailed logs/XML and preserved comparison journals are under `artifacts/company_simulator/`; `complete_acceptance/comparison.json` summarizes business goals independently from core correctness.

Prompt month: nine delivered goals met, one fully cancelled; 106 local messages (37 incoming / 69 simulated replies); all28 current planned flow families exercised, stock A4/B2, sales10/purchases4/ledger72 and cash190/receivable20. Shopify prompt fulfills all three delivery goals; idle still observes bank deposits and held/unallocated funds correctly. All modeled core reconciliations pass. These prove the stated profiles, not every possible business process or a real AI model's performance.

## Local correspondence script

The complete v2 profile adds customer deadline enquiries, cancellation and return messages; supplier confirmations, revised arrival dates and partial-receipt notices; and factual baseline-agent acknowledgements/accepted-action updates. Templates, addresses and release offsets live in `complete.yaml` under `correspondence`. Supplier notices appear one simulation day after an actual purchase, never before it. Delay dates become operator-visible only through a released notice. Messages alone do not fulfill stock or financial obligations.

All messages are immutable normal Sources with explicit party references and available order IDs, run-local thread/message/reply identities, and `transport: local_simulation`. `messages.jsonl` stores the source ID, direction and recorded state. `report.json.communication` counts incoming messages, simulated replies and reply drafts. In the UI, **Simulated locally · no real email sent** and **Reply draft · not sent** make the boundary visible. Idle operators produce no replies; custom operators produce only the drafts they explicitly return.

Example custom command: `{"kind": "reply", "message_id": "RELEASED_MESSAGE_ID", "subject": "Re: delivery enquiry", "body": "I will check the recorded shipment status."}`. This stores draft evidence without approving or sending mail. Real transport must follow the [canonical email handoff contract](../../../../docs/features/agent-email-handoffs.md); this local journal is not production approval/claim/report evidence. Historical v1 milestone totals remain valid for stock/finance, but communication counts and case coverage differ in v2.

### Live company stories

Start the read-only viewer with `python -m scenarios.company_simulator.viewer` from `packages/reality-core`, then open `http://127.0.0.1:8765/stories`. Select the run started by your simulator CLI. **Live watch** follows its newest complete checkpoint every five seconds. **Replay recording** plays only saved days. Browser Play/Pause control replay, never the simulator. See [viewer instructions](viewer/README.md) for unsupported profiles, observation freshness and Reality reference boundaries.

## Default operational coordination (spec 377)

Apply migration 0145 and run the shared scheduler/worker. Coordination is default for
all companies; no owner enable step. Read `operational_case_status` to distinguish
migration readiness and completed historical backfill from product policy. Accepted
orders and open return announcements receive their canonical cases. Raw mail does not.
Manual takeover, exact handback and fresh post-handback review remain mandatory.
External-runner and multi-day capacity gates remain pending.
