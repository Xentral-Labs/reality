# Implementation Plan: Demo Data pays its orders

**Branch**: `168-demo-order-to-cash` | **Date**: 2026-09-10 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Demo Data keeps producing orders as today. A second durable schedule walks the connection's
recent orders, recomputes each order's settlement plan from the run seed, and emits the
invoice and payment records that are due, through the normal `enqueue_source` intake. Two new
registered interpreters hand the lossless payloads to a new provider-agnostic module,
`services/payment_intake.py`, which posts the stated invoice, records every payment, allocates
only references the source states, and exposes read-time candidates for the rest. Confirmation
of a candidate reuses the spec 148 settlement flow in mode `allocate_credit`. One nullable
column on the connection, one migration, no new business table.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript for the integration panel
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, React/Vite
**Storage**: PostgreSQL; synthetic payloads stored losslessly as SourceRecords
**Testing**: pytest unit/service/story/adapter; web contract tests; saved browser script
**Project Type**: backend services plus the existing web integration panel
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope; no rate
arithmetic in services (spec 088 DR-007); no accelerated clock (spec 146)
**Scale/Scope**: one practice tenant per owner; at most 300 orders per hour, at most 10
settlement records per minute; scans bounded to the last 30 days of synthetic orders

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Invoice and payment are SourceRecords → ImportJobs → registered interpreters → Document/DocumentLine → LedgerEntry/SettlementAllocation. The job writes no business record; it calls `enqueue_source` and the bound processor only. | PASS |
| Reality owns operational state | Paid/partial/open, credit and candidates are derived at read time from ledger entries and allocations. No status column, no candidate table, no stored counter; the status block is computed from source records and read services. | PASS |
| Proven schema only | One nullable `settlement_schedule_id` on `demo_data_connection`, used by every control action to find, cancel and resume the second schedule (spec FR-019). Alternative without schema (fold into order job) rejected in decision 2. | PASS |
| Tenant + shared service boundaries | Every query joins on tenant; the settlement job authorises like the order job on each occurrence; interpreters run under a bound profile scope; HTTP adapters keep the existing tenant/run-prefix routers and call `services.demo_data` only. | PASS |
| Spec/test traceability | Test strategy table below maps each FR/DR to named test files; tests are written first for the planner, the core and the job. | PASS |
| Explainable web behavior | Status block links to Payments, Open Items and Journal filtered to the source; every synthetic record is reachable through the existing Source/ImportJob/document inspectors; candidates carry their reason. | PASS |
| Received values not recomputed | Amounts, references, dates and term code are taken from the payload as stated; the core never derives a discount or difference; candidates are observations with reasons, never authority. | PASS |
| Smallest coherent design | Reuses `record_customer_payment`, `allocate_settlement`, `post_sales_invoice`, `create_manual_document_with_lines`, the scheduler, `cancel_queued_run`, the 148 settlement flow and MCP tool. New code: planner, two producers, one module, one job, one column, one status block. | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/integrations/demo_data.py     # producer: settlement plan, invoice/payment payloads, normalisers
packages/reality-core/src/reality/services/payment_intake.py    # NEW shared core: normalised shapes, resolver, interpreters, candidates
packages/reality-core/src/reality/services/core.py              # SOURCE_INTERPRETERS entries; process_import_job_bound generalised
packages/reality-core/src/reality/services/tenant_policy.py     # _SETTLEMENT_OPERATIONS scope; require_demo_intake accepts it
packages/reality-core/src/reality/services/demo_data.py         # payment term prerequisite, settlement_scope, both schedules, status block
packages/reality-core/src/reality/jobs/handlers/demo_data.py    # SETTLE job definition
packages/reality-core/src/reality/jobs/registry.py              # register SETTLE
packages/reality-core/src/reality/db/demo_data.py               # settlement_schedule_id
packages/reality-core/migrations/versions/0055_demo_settlement_schedule.py
packages/reality-core/src/reality/web/api.py                    # GET payment candidates route
packages/reality-core/src/reality/mcp/catalog.py                # finance_payment_candidates read tool
packages/reality-core/src/reality/tools/finance.py              # candidates tool input
packages/reality-core/config/{connector,tenant_isolation,command}_catalog.yaml
apps/web/src/api.ts, apps/web/src/components/DemoDataIntegration.tsx, apps/web/src/localization.tsx
specs/146-company-setup-demo/{spec.md,contracts/demo-data.md}, docs/features/company-setup-demo.md
```

**Files/layers affected**: producer (`integrations/`) depends on nothing in `services/`;
`payment_intake.py` depends on `core.py` primitives only; `demo_data.py` and the job handler
depend on both; adapters depend on `services.demo_data` and `services.payment_intake`. No
service imports an adapter.

## Design

### Reality flow

```text
order SourceRecord {schedule}:{run}[:{position}]          exists today, one per order in a delivery burst
  -> settlement plan (pure, from seed + schedule + order external id)
  -> invoice  SourceRecord {order external id}:invoice      -> ImportJob -> interpret_sales_invoice
        Document sales_invoice (number, payment_term, source_record_id)
        DocumentLine per order line with billed_document_line_id
        LedgerEntry AR debit / revenue credit (post_sales_invoice)
  -> payment  SourceRecord {order external id}:payment:{n}  -> ImportJob -> interpret_customer_payment
        Document customer_payment (source_record_id)
        LedgerEntry cash debit / AR credit on the invoice's control account (record_customer_payment)
        SettlementAllocation payment AR entry -> invoice AR entry, min(unallocated, open)   [tier 2 only]
  -> candidates: read-time pairs (payment, invoice, reason)                                  [tier 3, never stored]
```

The spec's identity pattern `{schedule}:{run}:invoice` is refined to `{order external id}:invoice`
because a delivery may carry several orders whose ids end in `:{position}`; the spec text is
corrected alongside this plan.

### Producer: plan and payloads (`integrations/demo_data.py`)

- `OUTCOME_WEIGHTS`, `MONEY_PATH_WEIGHTS`, `DELAYS` module constants, the only place the
  version 1 table lives (spec FR-003, FR-008).
- `settlement_plan(seed, schedule_id, order_external_id, ordered_at, order_payload) -> SettlementPlan`
  (Pydantic, frozen). Draws use the existing `_draw` with purposes `settle:path`,
  `settle:outcome`, `settle:delay:{step}`, `settle:amount`. Fields: `money_path`, `outcome`,
  `invoice_at`, `payments: list[PlannedPayment]` with `n`, `at`, `amount` (stated Decimal),
  `references: list[{type, value}]`, `narrative` (remittance text). Amounts are computed here
  once from the order gross and written as facts; the outcome table decides shape, e.g.
  discount 2–3 % rounded to cents, withheld 0.50–6.00, partial 40–70 % then rest, typo
  rounds up to the next 10, duplicate repeats the amount.
- `produce` gains `shop_id` (`f"demo-{sha[:16]}"`), `customer_reference`
  (`PO-{deterministic}`) alongside the existing readable `number`; `DemoOrder` keeps schema
  version 1 with the new fields optional so stored payloads validate.
- `produce_invoice(order_payload, plan) -> dict` and `produce_payment(order_payload, invoice_payload, plan, n) -> dict`
  return lossless payloads with `schema_version: 1`, `synthetic: True`, `order_external_id`,
  and the field names of the bank-statement profile for payments (`payment_number`,
  `external_id`, `party_name`, `direction: "incoming"`, `amount`, `currency`, `effective_at`)
  plus `money_path`, `references`, `remittance_text`, `payment_index`.
- `DemoInvoice`, `DemoPayment` Pydantic models validate payloads; `normalise_invoice`,
  `normalise_payment` map them one to one to the shared shapes.
- `interpret_invoice`, `interpret_payment`: `require_demo_intake(..., settlement=True)`, then
  normaliser, then the shared core.

### Shared core (`services/payment_intake.py`)

- Shapes: `Reference(type: Literal[invoice_number, shop_id, shop_order_number, customer_reference, customer_number], value: str)`,
  `NormalisedInvoice(order_source: (system, type, external_id), number, party_id, currency, issued_at, due_at, payment_term_code, gross_amount, lines[...] with order_source_line_id, source-stated components)`,
  `NormalisedPayment(party_id, amount, currency, effective_at, external_payment_id, money_path, references, remittance_text, payment_number)`.
- `interpret_sales_invoice(session, tenant_id, source, normalised)`: replay check on
  `(source_record_id, type)`; resolve the order document via its SourceRecord; map each line's
  `order_source_line_id` to the order's `DocumentLine` and set `billed_document_line_id`;
  `create_manual_document_with_lines("sales_invoice", ..., payment_term_code=..., source_record_id=source.id, _commit=False)`;
  `post_sales_invoice(..., effective_at=issued_at, _commit=False)`. Returns
  `(source, document, lines, entries)`.
- `resolve_references(session, tenant_id, party_id, currency, references) -> Resolution`
  with `invoices: list[Document]`, `reasons: list[str]`, following the spec FR-012 table;
  `customer_number` narrows only. Posted and non-reversed filter via the invoice control
  entry.
- `interpret_customer_payment(session, tenant_id, source, normalised)`: replay check;
  `record_customer_payment(..., source_record_id=source.id, _control_account_id=<invoice control account when exactly one invoice resolves, else default>, _commit=False)`;
  if exactly one invoice: `allocate_settlement(payment_entry, invoice_entry, min(amount, open), _commit=False)`.
  Returns `(source, document, entries, allocation | None, resolution)`.
- `payment_candidates(session, tenant_id, payment_document_id) -> list[Candidate]`: unallocated
  amount from `payment_rows` logic; candidates by amount equality, invoice-number substring,
  ambiguous stated reference; each `{invoice_id, number, open_amount, reason}`. Pure read.
- No new business event: `document.recorded`, `ledger.posted`, `settlement.allocated` fire from
  the primitives and already invalidate Open items, Payments, Journal.

### Bound processing and policy (`services/core.py`, `services/tenant_policy.py`)

- `SOURCE_INTERPRETERS[("demo_data", "invoice")] = _demo_invoice_interpretation`,
  `SOURCE_INTERPRETERS[("demo_data", "payment")] = _demo_payment_interpretation`.
- `process_import_job_bound`: replace the single-pair guard with `SYNTHETIC_SOURCES = {("demo_data", t) for t in ("order", "invoice", "payment")}`;
  interpreter name and failure summary derived from `source.source_type`; savepoint semantics
  unchanged. Every path that indexes `SOURCE_INTERPRETERS[("demo_data", "order")]` (two places)
  uses the pair of the current source.
- `_SETTLEMENT_OPERATIONS = _INTAKE_OPERATIONS | {"create_document", "post_ledger", "post_sales_invoice", "record_customer_payment", "allocate_settlement"}`.
  `require_demo_intake(session, tenant_id, *, settlement=False)` accepts the settlement set
  only when asked. The order interpreter keeps `settlement=False`, so orders cannot book money
  even if mis-scheduled.
- `_CONNECT_OPERATIONS` gains `create_payment_term` for the prerequisite term.

### Demo Data service (`services/demo_data.py`)

- Preview/connect: prerequisite payment term `DEMO-14-2` ("14 days net, 2 % within 7 days",
  `due_days=14`, `discount_percent=2`, `discount_days=7`) added to `add`/`references` under
  `payment_terms`; matched by code when present. The fingerprint changes; existing connections
  re-preview on next control like any reference change.
- `settlement_scope`: like `intake_scope` with `_SETTLEMENT_OPERATIONS`.
- `_imports(session, tenant_id, *, source_types=("order",), job_types=("demo.generate_orders",))`
  generalised; `_import_classification` takes the document type per source type
  (`sales_order`, `sales_invoice`, `customer_payment`). Existing callers keep the order-only
  default so counters and pages do not change meaning.
- `control`: `start` creates the order schedule and the settlement schedule
  (`demo.settle_orders`, config `{connection_id, profile_version, references}`, `interval_seconds=60`);
  `pause/stop/disconnect` call `cancel_queued_run` on both; `resume` resumes both; `set_rate`
  touches the order schedule only; `stop`/`start` mint new ids for both. The saturation check
  counts all three types.
- `status`: adds `order_to_cash` with `invoices_issued`, `payments_received`,
  `payments_allocated`, `invoices_settled`, `open_residuals`, `credit_created`,
  `unmatched_payments`, `last_settlement`, `next_settlement`, all computed from `_imports` by
  type plus `open_invoice_amount`/`active_settlement_allocations` over the 30-day window.

### Job (`jobs/handlers/demo_data.py`)

- `SettleConfig(connection_id, profile_version=1, references)`; `authorize_settle` mirrors
  `authorize` but checks `connection.settlement_schedule_id == run.schedule_id`.
- `settle(session, context, config)`:
  1. `demo_data._locked`, authorise, saturation check (pause both when ≥ 20).
  2. Select synthetic orders of this connection with an interpreted outcome and a
     `sales_order` document, `ordered_at >= now - 30 days`, joined to their generating schedule
     to read `configuration.arguments.seed`.
  3. For each: `settlement_plan(...)`; due steps = invoice if `invoice_at <= now` and no
     `:invoice` record; payment `n` if the invoice record exists with `interpreted` outcome,
     `payments[n].at <= now` and no `:payment:{n}` record. Collect `(due_at, kind, order)`.
  4. Sort by `due_at`, take 10. For each, inside `settlement_scope`: `enqueue_source(...,
     _commit=False)` with the produced payload (or the stored one when the record exists but
     its job is not completed), then `process_import_job_bound`.
  5. Return `JobResult(counts={"invoices": i, "payments": p, "imported": ..., "failed": ..., "deferred": remaining})`
     and references.
- Paused time shifts nothing: due times are absolute, so after resume the backlog drains at
  25 per minute (spec FR-018, SC-005). The bound started at ten and was raised after the
  live run showed saturation at 300 orders per hour (five invoices plus five first payments).

### Candidate confirmation (adapters)

Implementation note (2026-09-10): instead of a new route and MCP tool, the existing
`settlement_context` read (HTTP `GET /finance/settlements/context/{document_id}` and MCP
`finance_settlement_context`) carries per-choice `reasons` and a `candidates` list for an
unallocated customer payment. The Payments register already offers "Use available credit" on
such a payment, which opens the guided flow in mode `allocate_credit`; the dialog now lists the
suggested invoices with their reasons. One read, one flow, no new command.

- `GET /api/tenants/{tenant_id}/finance/payments/{payment_document_id}/candidates` returns
  `payment_candidates`. MCP read tool `finance_payment_candidates` with the same shape.
- Confirmation: the existing `finance_settlement_propose` in mode `allocate_credit` with the
  payment's available credit and the chosen `invoice_id`; `apply_settlement` already composes
  `allocate_settlement` with the tier-2 bounds and records actor and action. No new command.
- Web: Payments page row action "Show candidates" listing candidates with reasons and a
  "Use this credit" button that opens the existing settlement dialog prefilled. Kept small;
  the browser script covers one case.

### Data and migration impact

- `DemoDataConnection.settlement_schedule_id: Mapped[str | None]`, no constraint change
  (running connections created before this feature keep `NULL` until the owner stops and
  starts; `control` treats `NULL` as "create on start").
- Migration `0055_demo_settlement_schedule` (`down_revision = "0054_target_mappings"`):
  `add_column` nullable; downgrade drops it. Additive; no data backfill.
- Catalogs: `connector_catalog.yaml` capabilities `{order: sales_order, invoice: sales_invoice, payment: payment}`;
  `tenant_isolation_catalog.yaml` adds `settlement_scope`, the job, `payment_intake` operations
  and the candidates route; `command_catalog.yaml` unchanged (no new mutation);
  `docs/DATA_MODEL.md` note for the column; `SPEC_COVERAGE_MATRIX.md` rows for new tests.

### Failure, security, and tenant behavior

- Authorisation on every occurrence: owner eligibility, connection identity, source active,
  references fingerprint, schedule identity, running state; `JobError` codes reused.
- Validation failure of one record: savepoint rollback, `failed` outcome, source retained,
  occurrence continues with the next record; unexpected error propagates and rolls the
  occurrence back, all identities retried.
- Idempotency: SourceRecord identity per step; a retried occurrence finds the records and
  processes only jobs not yet completed; replay of an interpreter returns existing records.
- Cross-tenant/party/currency: `resolve_references` filters by tenant and party; currency
  mismatch yields no tier-2 allocation and a candidate reason; `allocate_settlement` re-checks
  account, party, currency and bounds.
- Blocked receivable account: `record_customer_payment` resolves an allowed account; the
  allocation is skipped and the payment stays as credit.
- Confirmation: candidates are read-only; every allocation from a candidate goes through the
  confirmed settlement proposal with revision check.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | unit | `tests/test_integrations.py::test_demo_data_declares_invoice_and_payment_capabilities` | capability set is `{order}` |
| FR-002, FR-003, FR-004 | unit | `tests/test_demo_data_settlement_plan.py`: determinism, 10,000-seed distribution within 1 pp, differences only on bank path, amounts are stated Decimals | module missing |
| FR-005, FR-006 | unit | `tests/test_demo_data_settlement_plan.py::test_payloads_carry_identities_and_references` | producers missing |
| FR-007 | service | `tests/test_demo_data.py::test_connect_adds_or_matches_discount_payment_term` | preview lacks `payment_terms` |
| FR-008 | unit | `tests/test_demo_data_settlement_plan.py::test_delays_are_ordered_and_compressed` | module missing |
| FR-009 | service | `tests/test_payment_intake.py::test_invoice_core_links_lines_and_posts_once` | module missing |
| FR-010–FR-013 | service | `tests/test_payment_intake.py`: exact, short, over, unmatched, second payment, wrong currency, wrong party, replay, blocked account, unposted invoice | module missing |
| FR-012 | service | `tests/test_payment_intake.py::test_references_resolve_by_type_and_ambiguity_yields_none` | resolver missing |
| FR-014 | service | `tests/test_payment_intake.py::test_candidates_have_reasons_and_write_nothing` (row counts before/after) | function missing |
| FR-015 | adapter | `tests/test_ai_mcp.py::test_payment_candidates_tool_and_allocate_credit_confirmation`; `tests/test_http_boundary.py` route | tool unknown |
| FR-016 | unit | `tests/finance/test_component_boundaries.py::test_payment_intake_imports_only_core` | module missing |
| FR-017 | service | `tests/test_demo_data_intake.py::test_bound_processing_accepts_all_synthetic_types` | guard refuses invoice |
| FR-018 | job | `tests/test_demo_data_intake.py::test_settlement_occurrence_emits_due_records_in_bounded_batches` | job type unknown |
| FR-019 | service | `tests/test_demo_data.py::test_controls_manage_both_schedules_and_set_rate_leaves_settlement` | column missing |
| FR-020 | job | `tests/test_demo_data_intake.py::test_saturation_counts_all_types_and_pauses_both` | counts orders only |
| FR-021 | security | `tests/test_demo_data_security.py::test_order_scope_cannot_post_money_and_settlement_scope_is_bounded` | scope set missing |
| FR-022 | review | spec 146 amendment reviewed in PR; `make spec-check` | text says never pays |
| FR-023 | service | `tests/test_demo_data.py::test_status_reports_order_to_cash_observations` | key missing |
| FR-024 | adapter | `apps/web/scripts/demo-entrypoint-contract.test.mjs` extended; `apps/web/scripts/demo-data-payments-browser.mjs`; `i18n` audit | keys missing |
| FR-025 | service | `tests/operational_exceptions/test_payment_differences_from_demo.py` | none raised without records |
| DR-001–DR-003 | story | `tests/scenarios/test_demo_order_to_cash.py`: order → invoice → exact/short/over/unmatched → open items, credit, candidates, confirmation | module missing |
| DR-004 | isolation | `tests/tenant_isolation/` catalog entries for new operations | catalog incomplete |
| DR-005 | migration | `tests/test_company_setup_migration.py` round trip 0054 ↔ 0055 | revision unknown |
| DR-006 | unit | boundary test above; `integrations/demo_data.py` imports no `services` symbol at module level except the existing lazy imports | none |
| DR-007 | unit | `tests/test_demo_data_settlement_plan.py::test_no_rate_arithmetic_in_services` (AST walk like spec 088) | none |

Tests are written before the corresponding implementation slice; the planner and core tests
run without the scheduler.

## Rollout and Rollback

- Order of work: producer and planner → `payment_intake` core → policy and bound processing →
  Demo Data service and job → migration → adapters and web → catalogs and spec 146 amendment →
  browser script and docs.
- Deploy API, scheduler and worker from one revision; apply 0055 once. Existing connections
  continue producing orders; the settlement stream begins after the owner's next stop and
  start (documented in the panel).
- Observability: `JobResult.counts` per occurrence, status block, existing scheduler run rows.
- Rollback: disable by stopping the connection; downgrade 0055 drops the column; recorded
  invoices, payments and allocations remain valid business history and need no removal.

## Review Risks

- Widening intake authority: the settlement scope must stay unreachable from the order
  interpreter and from any public API; security tests are the gate.
- Reference resolution over `Document.number` must be party-scoped; a global lookup would leak
  across customers.
- Status computations over open amounts can grow; the 30-day window and count-only semantics
  keep them bounded, and they are observations only.
- Spec 146 contract already lags the code (bursts of several orders per occurrence); the
  amendment must describe the current behaviour, not only add payments.
- The stacked branch (on 165) must be rebased onto main once 165 merges before a PR.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
