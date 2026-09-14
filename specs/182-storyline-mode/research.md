# Research: Storyline Mode

**Date**: 2026-09-12 | **Spec**: [spec.md](spec.md)

Facts established by reading the code on `main` (commit `1f76c1e`). Each item names the file the
plan relies on. Nothing here is a decision; decisions are in [plan.md](plan.md).

## R1. The Playground engine is intact and reusable

- `db/core.py:161-222` `PlaygroundRun` (`preset_key`, `sandbox_kind` temporary|practice,
  `preset_version`, `lesson_key`, `lesson_version`, `client_request_key`, `status`,
  `initialization_progress` JSONB ≤ 64 KiB, `ready_at`, `archived_at`; unique per tenant; one
  active temporary run per owner). No column for a storyline key, a current chapter, a branch
  or a sequence marker.
- `db/core.py:225-267` `PlaygroundStep` (`run_id`, `sequence`, `request_key`, `proposal_id`
  with composite FK to `action`, `lesson_step_key` String(80) nullable, `before_observation`
  and `receipt_observation` JSONB ≤ 64 KiB). One step per proposal; one proposal per step.
- `services/playground.py`: `start_run` :1634, `restart_run` :1770, `prepare_step` :934,
  `confirm_step` :569, `reject_step` :823, `read_step` :433, `read_reality` :457,
  `read_run` :1465, `list_runs` :1495. `confirm_step` already stores a receipt with
  `records`, `event_ids` and `event_sequence` (:770-825). Three idempotency layers:
  `(owner, client_request_key)`, `(run, request_key)`, `preview_revision` hash.
- `prepare_step` maps lesson tools through a hard-coded chain (:958-983) onto bespoke
  Pydantic inputs in `playground/actions.py`; any other tool raises "This guided action is
  not available yet." Time inputs accepted: `occurred_at` on movements, `effective_at` on
  invoices and payments; the order input has no date field.
- Quotas: `REALITY_PLAYGROUND_DAILY_RUN_LIMIT` 5, `RETAINED_RUN_LIMIT` 20, `STEP_LIMIT` 50
  executed proposals per tenant, `REALITY_PLAYGROUND_ENABLED` gate (:1408-1446).
- `web/playground.py` keeps the `/api/playground` router with start, restart, prepare,
  confirm, reject, read and chat routes; only the browser URLs are retired
  (`apps/web/src/entryRouting.ts:51-52`, `tests/test_http_boundary.py:213`).
- Practice companies: `start_run` creates `Tenant(purpose="playground")`; profile presets
  require `sandbox_kind="practice"` (:1692). `services/company_setup.py:292 initialize_profile`
  seeds inside `session.begin_nested()` and resets the run to `initialization_failed` on any
  error, which is the one-unit rollback the spec's edge case asks for.

## R2. Tool dispatch has no trace surface, and the web does not use `run_read_tool`

- `tools/application.py:2102 run_read_tool(session, tenant_id, tool_name, arguments)` has no
  actor, principal, timing or result interception. `create_change_proposal` :2376 and
  `approve_and_execute_proposal` :2595 take a `Principal` only on decision.
- Ambient context exists only as authority `ContextVar`s in `services/tenant_policy.py`
  (`_seed_authority`, `_proposal_authority`, `_decision_authority`, …), which the Playground
  already enters around seeding and decisions.
- `run_read_tool` is called by `services/playground.py` and `mcp/catalog.py` only. Browser
  reads go from `web/api.py` endpoints straight to services. A trace hung on `run_read_tool`
  would capture Copilot and MCP reads but not app views.
- Every tenant route already carries `Depends(require_tenant_surface_access)`
  (`web/api.py:312-316`), a natural place for a per-request recorder.

## R3. Events carry the proposal; Facts carry no recording order

- `BusinessEvent` (`db/core.py:1543`): per-tenant monotonic `sequence`, `recorded_at`,
  `action_id`, `causation_id`, `correlation_id`. `services/core.py:434 business_events(...,
  after_sequence)` is a forward read; `timeline_activity` :12490 pages backwards only
  (`before_sequence`) and enriches items with names and titles; `activity_signal` :461 returns
  `latest_sequence` for a cursor.
- `Fact` (`db/core.py:1390`): `observed_at` only, random ids, no `recorded_at`, no
  `action_id`. `services/core.py:555 observe_fact` accepts `action_id` and drops it. The
  spec's fallback applies: a recording order must be added.
- `ChangeProposal` (`db/core.py:1512`, table `action`): `type = "tool:<name>"`, `input`,
  `output`, `status`, `decided_at`, `decided_by_user_id`.

## R4. Exceptions are derived snapshots; there is no record-link service

- No exception table. `services/exceptions.py:3098 operational_exceptions(session, tenant_id,
  as_of)` derives all findings; identity is `exc__<class>__<record>` (:133).
  `services/attention_reads.py` exposes `attention_summary` :86, `attention_register` :109,
  `attention_detail` :158 (guidance from `clears_through`). Raised and cleared can only be
  computed by comparing two snapshots.
- 35 classes in `config/operational_exception_catalog.yaml`. Relevant to the storyline:
  `reservation_exceeds_stock`, `outgoing_commitment_at_risk`, `order_stalled`,
  `overdue_incoming_supplier_commitment`, `party_hold_unreleased`, `commitment_hold_unreleased`,
  `overdue_receivable`, `credit_limit_exceeded`, `unmatched_financial_event`,
  `credit_note_unsettled`. The example ids in the spec's YAML (`stock_short`) do not exist.
- No `record_link` table and no graph read. The Context Graph tab is fed by the per-kind
  inspector builders (`web/api.py:4781-5932`) and the typed explorer read (:6476,
  `services/inspector_register.py:86`). Edges are assembled per builder.

## R5. Catalog, labels and docs

- `catalogs.py:1202 load_application_catalog()` validates the four YAML catalogs against the
  code; `tests/test_application_catalog.py:13` pins 91 commands, 60 events, 13 projections,
  7 predicates and the ordered exception class list. Any new command changes these counts.
- View keys live in `config/workspace_catalog.yaml:3-21` (`orders`, `open_items`,
  `fulfillment_blockers`, `payments`, `commitments`, …). Process steps for `order_to_cash` are
  in `config/resource_catalog.yaml:340-380`.
- Per-language labels: `resource_catalog.yaml` `labels.de` covers commands, views,
  projections, exceptions and workspaces in German only; the web's
  `GET /application-reference` (`web/api.py:3334`) returns English only; only
  `GET /api/playground/exception-catalog` returns labels per language. Spec 178 FR-007 set the
  precedent: labels in the UI language where the catalog has one, descriptions in the
  catalog's language.
- Docs: `apps/docs/scripts/generate-catalog-reference.py` writes `tool-usage.json` and the EN
  and DE Tool Usage pages; `docs-contract.test.mjs:230` requires a DE twin for every EN page;
  absolute links to `content/public/` files pass the link test; CI rejects stale generated
  output for `content/tool-usage`, `content/de/tool-usage` and `.vitepress/data` only
  (`quality.yml:213`).
- Versioned seed precedent: `demo/profile_contract.py` `ProfileManifest` with `extra="forbid"`
  and a 60 000 byte bound; profile version is written into each seeded source payload and
  into `run.initialization_progress["profile"]`, not onto the tenant.
- PyYAML and Pydantic v2 are runtime dependencies. No JSON Schema files exist in the repo.

## R6. Web app shape

- Routing (`apps/web/src/unified/routing.ts`): a destination touches the union (1-16), the
  route list (74-91), the whitelist and field parsing in `readSelection` (95-256), the
  `selectionUrl` block (257-337), `companySelection` (338-376) and `entryRouting.ts:2-18`.
- `UnifiedApp.tsx:127-277` mounts one page per route; pages receive `selection` and
  `navigate` as props, so a page can be mounted with a synthesized selection. Register and
  page headers portal into Shell targets (`Shell.tsx:191-193`, 576-579); an embedded page
  needs its own target providers or its header lands in the Shell header.
- The Shell's right dock is the compact chat (`Shell.tsx:582-599`), forced open on the
  Copilot route; there is no per-route slot. Demo Data nav gating: `company.company_kind ===
  "demo" || company.demo_data_state` (:551). `company_kind` is `company | sandbox | demo`.
- Proposal cards (`ActionCard.tsx:777-837` dispatcher; `OrderCard`, `PaymentCard`, …) seed
  their draft from a literal; no card accepts prefilled values. Opening a card with
  `proposalId` loads the prepared proposal through `deliveryActions.review` and renders the
  review with confirm and reject, bypassing the form.
- `api.timeline` (`api.ts:1474`) has `beforeSequence` only; `api.activitySignal` (:1496) takes
  `afterSequence`. No shared polling hook; `HomePulse.tsx:60-113` is the polling precedent.
- Stepper precedent: `FactRuleWizard.tsx:228-250` with `aria-current="step"` and
  `data-stage`; `ruleWizardState.ts` derives the stage from server state.
- i18n: `localization.tsx` with `Object.assign(dictionaries.de, {...})` blocks; the audit
  (`scripts/i18n-audit-lib.mjs`) fails on missing, identical or protected-term-dropping
  translations in de, nl, es. Docs have EN and DE only; the app has four languages.
- Tests: Node contract tests in `apps/web/scripts/*.test.mjs` (`product-boundary.test.mjs`
  forbids `src/playground`), Playwright scripts against a running Vite on 5177 with all API
  traffic mocked; the 390 px overflow assertion pattern is in
  `unified-activity-browser.mjs:261-296`.
- Download precedent: CSV Blob in `RegisterTable.tsx:200-219`; upload precedent: raw-body
  `POST …/item-imports/artifacts?filename=` in `api.ts:2522` with `<input type="file">` in
  `ItemImportPanel.tsx:235-249`.

## R7. Command coverage of the seven chapters

| Chapter | Tool today | Note |
| --- | --- | --- |
| Create order | `order_create` (sales) | exists |
| Short goods receipt | `movement_create` receipt against a purchase commitment, or `shipment_receive` | exists; needs a seeded purchase order |
| Release blocked shipment | `shipment_dispatch` gated by `services/delivery_actions.py` release review; hold via `party_delivery_hold` | exists; the hold must be seeded, it is not automatic |
| Dunning notice | none (`dunning`, `reminder` have zero hits) | **missing** |
| Record overpayment | `customer_payment_post` with `effective_at` | exists; residual visible through `finance.credits.list`, `unmatched_financial_event` |
| Reorder | `order_create` (purchase) | exists |
| Close period | none; no period record anywhere | **missing** |

An invoice's due date comes from its payment term, not from the invoice command; a backdated
`effective_at` plus a 14-day term yields an overdue receivable.

## R8. Hand-play of the chapters (T001, T002) — 2026-09-12

Played through `propose_tool` and `confirm_tool` against the real services on an isolated
PostgreSQL (`tests` fixtures `session`, `business`), every step confirmed with `confirmed=True`
and the delivery review token where present. Exception ids are the live `exceptions` read
after each step. The run script was temporary and is not committed; the condensed log is
reproduced here.

### What the seed can and cannot do

| Seed entry | Command and decisive input | Result |
| --- | --- | --- |
| Payment term | `payment_term_create {code: NET14, due_days: 14}` | record `payment_term` |
| Opening stock 8 | `movement_create {movement_type: opening_stock, item_id, quantity, to_location_id, occurred_at: -60d}` | backdating works |
| Overdue invoice | `document_create {document_type: sales_invoice, number, party_id, gross_amount, document_date: -56d, payment_term_code: NET14, lines[…]}` then `sales_invoice_post {document_id, effective_at: -56d}` | due date = `document_date + due_days` (`invoice_due_date`); **`overdue_receivable` raised immediately** |
| Customer hold | `party_delivery_hold {party_id, reason_code, note}`; reason codes: `address_clarification, compliance, credit_check, customer_request, manual_review, other` | record `party_hold`; **cannot be backdated** (no date input, `created_at = now`) |
| Purchase order 20 | `order_create {direction: purchase, number, company_party_id, counterparty_id, location_id, gross_amount, document_date: -14d, requested_delivery_at: -7d, lines[{item_id, quantity, unit, unit_price, gross_amount, promised_at}]}` | `overdue_incoming_supplier_commitment` raised (promised date passed) |

`record_sales_invoice` needs an order line; `document_create` is the right seed command for
an invoice with its own date and term. `customer_payment_post` refuses any amount above the
open receivable ("Payment exceeds the open invoice amount").

### What each chapter did

| # | Command and decisive input | Raised | Cleared | Notes |
| --- | --- | --- | --- | --- |
| 1 Order 12 | `order_create {direction: sales, …, requested_delivery_at: +5d, lines[{quantity: 12, promised_at: +5d}]}` → `commitment_ids[0]` | `outgoing_commitment_at_risk` (commitment) | | stock 8 < 12; raised without any reservation |
| 2 Short receipt 16 of 20 | `movement_create {movement_type: receipt, item_id, quantity: 16, to_location_id, commitment_id: <purchase commitment>}` | | | `overdue_incoming_supplier_commitment` **stays** with 4 open: this is the "short delivery" finding; at-risk stays because nothing is reserved yet |
| 3 Reserve | `reserve {commitment_id}` → `reserved, shortage` | | `outgoing_commitment_at_risk` once shortage is 0 | before the receipt a reserve gives `reserved 8, shortage 4` and at-risk stays; `reservation_exceeds_stock` never appeared |
| 4 Dispatch attempt | `movement_create {movement_type: shipment, quantity: 12, from_location_id, commitment_id}` | | | **refused at preparation**, no proposal exists: `InvalidOperation: Customer has an active delivery hold; release it before shipment.` The stored `fulfillment_blockers` projection lists the reason `party_delivery_hold` once refreshed |
| 5 Explain (read) | `exception_explain {exception_id: exc__overdue_receivable__<doc>}`, `finance.party_balances.list {side: customer}` (shows `overdue 1180`), live blockers | | | `party_hold_unreleased` is **not** raised for a fresh hold: the derivation requires the hold to stand longer than a learned threshold (`_unreleased_hold_exceptions`), and holds cannot be backdated |
| 6 Overpayment 1 300 on 1 180 | read `finance.settlement.context {document_id}` → `revision`; then `finance.settlement.apply {expected_revision, document_id, mode: payment, amount: "1300.00", allocation_amount: "1180.00", reference, effective_at}` | `unmatched_financial_event` (cash ledger entry with 120 unallocated) | `overdue_receivable` | `finance.credits.list` shows `original 1300, used 1180, available 120, state partial`; party balance `credit 120, balance -120` |
| 7 Release hold | `party_delivery_hold_release {party_id}` | | | holds are manual; nothing releases them on payment |
| 8 Ship | `movement_create {movement_type: shipment, …}` | `shipped_not_billed` (order line) | | now succeeds |
| 9 Bill the order | `sales_invoice_record {order_line_id, quantity, gross_amount, number}` (not played; the class's `clears_through` names it) | | `shipped_not_billed` | candidate chapter that closes the loop |
| 10 Reorder 40 | `order_create {direction: purchase, …, requested_delivery_at: +10d}` | | | no reorder-point class exists; the explanation talks about expected incoming |
| 11 Month-end review (read) | `exceptions`, `finance.party_balances.list`, `commitments` | | | `stale_closure_preview {direction: sales|purchase, due_before}` returned 0; `item_supply_demand` and `fulfillment_blockers` are **stored** projections and empty until the background refresh ran: read chapters must use live reads or the explicit live mode |

Final open findings after chapter 10: `overdue_incoming_supplier_commitment` (4 open),
`shipped_not_billed` (until chapter 9), `unmatched_financial_event` (120 credit).

### Consequences for the design

- Chapter inputs need a value read at preparation time: `expected_revision` from
  `finance.settlement.context`. The package gets a `$context.<read>.<field>` reference that
  the service resolves at prepare and records in the trace.
- A refused preparation is a legitimate chapter outcome (chapter 4). The protocol shows the
  propose call with its error; the delta stays empty; the narrator explains the refusal. The
  spec's "blocked, not aborted" wording is corrected to "refused with the hold as the reason".
- Nothing cascades on payment: the hold release is its own chapter and the shipment its own.
  The story grows from seven to eleven chapters, three of them reads, and closes the loop
  with billing the shipped order.
- `party_hold_unreleased` cannot be shown in a fresh company; the hold is explained through
  the overdue receivable, the party balance and the blockers view instead.
- Reads inside chapters use live reads (`exceptions`, `commitments`, finance lists) or the
  explicit live mode of stored projections; the stage view may show a stored projection with
  its freshness notice.
- `overdue_incoming_supplier_commitment` plays the "delivery short" finding; no dedicated
  short-delivery class is needed.

### R8 addendum (2026-09-13, scenario test)

- A refund of a credit (`finance.settlement.apply`, `mode: refund_credit`) clears the
  `unmatched_financial_event` finding on the incoming payment and raises a new one on the
  refund's outgoing cash entry ("120.0000 EUR remains unallocated"), because the derivation
  counts every cash control entry that gave nothing to an invoice. The storyline says so in
  the refund chapter. Whether a refund against a credit should count as unmatched is a
  question for the exception catalog, not for this feature.
- The default path and both alternative paths play end to end through the service; every
  business event after the seed appears in exactly one chapter's delta (SC-002).

## R9: Purchase to pay, hand-played 2026-09-13

The second built-in storyline was played against the services before it was written. What
the services actually do, and what the storyline does about it:

- `supplier_invoice_record` records and posts in one step and refuses a second invoice
  against the same order line ("Invoice quantity exceeds the remaining billable quantity").
  The storyline therefore records invoices with `document_create` (type `supplier_invoice`,
  a line with `billed_document_line_id` and `unit_price`) and books them with
  `supplier_invoice_post`, which is also what makes "invoice price differs" comparable.
- `invoice_price_differs` compares the invoice line's `unit_price` with the agreed line;
  `billed_not_received` compares billed against received quantity per order line. A credit
  note for the missing ten clears the payable, not the quantity finding; only goods or a
  corrected invoice do. The credit branch says so.
- `document_lines_correct` refuses documents that carry Source evidence ("External evidence
  cannot be overwritten"), which manual orders do. Agreeing a new price on the order is
  therefore not a chapter; the price dispute is the one finding that remains at month-end.
- Finance commands refuse to run inside the seed ("Finance changes require a confirmed
  proposal"), so `finance.account.initialize` is a chapter with a context read of
  `finance.accounts.list` for its revision, placed where the discount finding first appears.
  A fresh practice company has defaults for receivables, payables, cash, revenue and
  inventory, but none for the reduction accounts.
- `ledger_reverse` names a posting group; no read tool exposed it. The posting outputs of
  invoices and credit notes now carry `posting_group_id` beside their ledger entries
  (additive, `_posting_result` in `tools/application.py`), and the storyline reverses the
  duplicate through it.
- `finance.adjustment.accept` needs `agreement` for a supplier discount; the seed's opening
  stock must be `opening_stock`, a `receipt` without a commitment raises
  `unexplained_movement`.

