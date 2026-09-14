# Implementation Plan: Operational Finance Subledgers

**Feature**: `148-accounting-journal-cost-centers` | **Date**: 2026-09-09 | **Spec**: [spec.md](spec.md)

**Status**: Accounts, available credit, accepted reductions, guided settlement, opening positions and managed finance references are integrated, verified and running on local port 8080. Received-component assignments and the 14-operation matrix are also verified and deployed. Source/case/target-account mapping is also verified and deployed. External handoff remains open; see [verification-results.md](verification-results.md).

**Checkout**: Assessed root workspace at detached HEAD `58dce63`, with concurrent uncommitted changes. The setup script resolved feature name 148; this is not evidence that a Git branch was created. No other worktree, branch, database or concurrent feature is adopted by this plan.

## Local development cutover decision — 2026-09-09

The owner is the only current local tester and has no real account population to migrate. Build a clean new schema and regenerate disposable test fixtures. No old-account-string backfill, unresolved legacy-account state, dual account columns, old-binary compatibility or per-tenant migration rollout is required. Keep the repository Alembic chain coherent; do not rewrite unrelated migration history. A reset/reseed must target an explicitly identified disposable local/test database and must not occur automatically on application startup or against an arbitrary configured database. This planning change does not execute a reset.

This removes local development compatibility work, not business integrity: newly recorded evidence/entries remain immutable and tenant-scoped, with explicit reversals. Customer/supplier opening imports, external historical-source matching and coverage remain product features for customers moving from other systems.

## Summary

Extend existing operational LedgerEntry, SettlementAllocation and LedgerReversal services into controlled customer and supplier subledgers. Add a small account catalog, received financial components and optional attribution, explicit settlement differences, opening positions and trade-finance controls. Prepare reproducible neutral accounting packages for external software. Preserve separate authorities for source evidence, internal decisions, operational entries and externally stated outcomes.

Deliver foundations first, then complete end-to-end business slices. No general ledger, financial closing, tax determination, revenue recognition, automatic currency conversion or calculated profit is introduced. The approved product scope remains in [spec.md](spec.md); the implementation decisions below refine it.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript and React 19 in the existing web application.  
**Primary Dependencies**: Existing SQLAlchemy 2, Alembic, psycopg, Pydantic v2, FastAPI, Typer, pytest, Vite and shared scheduler/worker. No new infrastructure or dependency required.  
**Storage**: PostgreSQL only; reuse SourceRecord/SourceArtifact for supplied payloads. Immutable bounded package JSON stored in PostgreSQL.  
**Testing**: PostgreSQL integration/concurrency/migration tests; independently authored business stories; tool/API/CLI/MCP contracts; web build, localization, component contracts and browser verification.  
**Constraints**: Decimal, UTC, tenant-scoped opaque IDs, received-value fidelity, explicit mutation authority, existing design system.  
**Bounds**: V1 imports/preparations at most 200 items and 4 MiB canonical UTF-8 JSON per request; reads default 50/max 200 rows; automatic drain at most 20 items/25 seconds per invocation. Larger work is explicitly partitioned without presenting partial success as an atomic batch.

## Constitution Check

Evaluated before and after design. PASS means this design meets the principle, not that implementation or schema approval is complete.

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Evidence extensions reuse Documents/Lines; posting provenance and receipt sources remain distinct; data-model.md | PASS |
| Reality owns operational state | Availability and readiness derived from entries, allocations and controls; no Document payment/fulfilment flags | PASS |
| Proven schema only | Each table group has FR justification and shortest-link constraints in data-model.md | PASS |
| Tenant + shared services | Composite tenant links, common transaction boundary and public command contracts | PASS |
| Spec/test traceability | All 58 FR and 7 DR individually mapped in verification.md and test-plan.md | PASS |
| Explainable web behavior | V01–V13 use shared read contracts and provenance links; contracts/views.md | PASS |
| Received values not recomputed | Nullable received components; no net/tax/FX reconstruction; assignment totals only derived | PASS |
| Smallest coherent design | Reuse ledger, evidence, proposals and shared jobs; alternatives recorded in research.md | PASS |

## Repository Structure and Layer Changes

Paths below are planned additions unless already present. Implement domain → services → tools → adapters; tests precede the behavior they prove.

| Layer | Paths and responsibility |
|---|---|
| Domain | `packages/reality-core/src/reality/domain/finance.py`: bounded roles, origin/direction rules, exact mapping match, amount-basis validation |
| Persistence | `packages/reality-core/src/reality/db/finance.py`, explicit metadata import in `db/core.py`; required `LedgerEntry.account_id`, replacing the old string field; Alembic revisions under existing migrations |
| Services | `packages/reality-core/src/reality/services/finance/{accounts,components,recording,settlement,opening,money,controls,handoff,reads}.py`: focused use cases and a common finance transaction helper |
| Existing service integration | `services/core.py`: invoice/payment/refund/reversal/allocation primitives and partial order billing; existing payment-run functions in `services/core.py`; no duplicate posting engine |
| Tools | `tools/finance.py` and registration in `tools/application.py`; extend proposal execution to commit financial effects and terminal result atomically |
| Catalogs | Existing command, projection, event, workspace and tenant-isolation catalogs; `catalogs.py` imports; each new business table and public command is discoverable |
| Adapters | Existing CLI, MCP and `web/` routers invoke the same tools; preserve old command contracts unless explicitly extended |
| Automation | New financial outbox drain handler in existing job registry; existing scheduler and worker deployment roles |
| Web | New `apps/web/src/finance/` modules, mounted through the current root `App.tsx`; reuse current headers, tables, dialogs, Inspector and styles rather than duplicating their behavior |
| Documentation | Update `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/WEB_SPEC.md`, relevant finance feature docs and `docs/features/scheduled-jobs.md` during the corresponding implemented slice |

The separately inspected unified-shell worktree is not the root baseline. Keep new finance presentation modular; if that shell lands before implementation, change only mounting paths after re-reading the integration checkout. Migration revision numbers are chosen against the actual head during implementation, not reserved over concurrent features 146/147.

## Design

### Reality flow

SourceRecord → existing Document/DocumentLine → received component or narrow evidence extension → existing balanced LedgerEntry group → effective SettlementAllocation/Reversal. Internal adjustments, opening declarations and transfers use explicitly internal or imported evidence kinds, never pretend to be external invoices. Optional source matches attach additional evidence to one effect, not another original posting.

The exact roles, fields and constraints are in [data-model.md](data-model.md). The eight standard ERP directions remain [posting-matrix.md](posting-matrix.md). Cost assignment is component attribution, independent of gross subledger posting. Exact source-code → local-reference classification has its own target-independent revisions; external destination mappings remain separately target-scoped. Money accounts may hold multiple currencies; entries/events own currency and all reads/settlements partition by it. PSP/advance/hold/transfer semantics remain [trade-finance-controls.md](trade-finance-controls.md).

### Service and adapter flow

Every write validates tenant, authority, idempotency and expected revision, locks the tenant finance coordination row, then re-reads availability/configuration before posting. It returns authoritative affected IDs and exact amounts. The transaction commits entries, allocations, evidence decisions, events and operation result together. Existing wrappers must accept transaction-bound execution without intermediate commits. All legacy finance write paths join the same serialization boundary before enabling new commands.

Chat/MCP use existing preview/proposal/confirmation; agents cannot approve their own proposals. A finance proposal executes its effects and final outcome within the bound transaction. Do not reuse the existing intermediate-commit flow without changing its finance branch. Workers execute only an explicitly enabled owner-approved recording authority, never approve arbitrary proposals.

Successful financial interpretation writes its recording outbox row in the evidence transaction. A registered recurring drain consumes eligible rows through the same service. Authority creation also registers the drain schedule; pause/revoke prevents new execution. No per-subsystem timers, network sender, worker migration or direct external-effect handler. See [contracts/commands.md](contracts/commands.md).

### Data and migration impact

Use the owner-approved clean local cutover. Replace the old account string with a required account_id directly, recreate disposable financial fixtures and remove legacy filters/callers. No nullable transition, account backfill, unresolved-role UI or compatibility column. Preserve the Alembic chain; use an explicit guarded local reset/reseed when necessary. New-model histories remain immutable.

Migrate in dependency order: (A) catalog/link/coordination/effect identity; (B) settlement/opening evidence; (C) received components/references and target/profile schema, then external account mappings and source-classification revisions; (D) handoff; (E) money/control evidence; (F) recording authority/outbox support. Only completed commands are registered; no per-tenant migration rollout state is needed. Exact next Alembic identifiers must follow the then-current migration head. New fixtures create effect identities through the shared services; external-source ambiguity still requires review.

### Failure, security, and tenant behavior

Cross-tenant IDs behave as unavailable. Composite tenant FKs and tenant-filtered repositories back service checks. Owner configuration, permission changes, account blocking, holds, consumption and automatic authority revocation serialize with financial writes. All endpoints use Decimal strings, not JSON floats.

Request idempotency and economic effect identity are different: replaying a request returns its stored result; different evidence for the same economic event matches the existing effect or produces review. Changed payload under an existing request ID conflicts. Unsupported semantics, currency exchange, contradictory matches or ambiguous history produce structured review reasons without discarding source evidence.

Full read totals and pages use one read-only REPEATABLE READ snapshot. Cursor continuation rejects changes to relevant finance revision or tenant event sequence. Reads never refresh/commit materialized projections. No persistent balance, readiness or derived financial Fact authority is introduced.

## Test Strategy and Traceability

[test-plan.md](test-plan.md) assigns every requirement an exact planned test file and initially missing behavior. [verification.md](verification.md) supplies the independent acceptance fixtures. The implementation tasks must give individual test names and observe meaningful failures before each slice.

Required risk proofs include concurrent allocation versus refund/earmark/reversal; blocked-account versus posting; hold versus execution; stale mapping/proposal; crash after evidence commit; retry after committed effect/lost response; mixed-origin availability; both supplier/customer signs; tenant isolation; clean initialization, required account links and new-model history; read-only snapshots and partial billing.

## Delivery Sequence

1. **Foundation**: regression tests; account catalog/defaults without an external target dependency; direct required account links; atomic common write boundary; economic/request identity; role-wide discovery and generic control-entry availability.
2. **Customer and supplier settlement**: actual money, explicit agreed reductions, credits, refunds, reversals, cross-account transfer; V02/V03/V08/V09.
3. **Opening positions**: preview, cutover coverage/deduplication and four-direction import; V10 and credit integration.
4. **Received detail and handoff**: components, centers, target/profile schema before external account mappings, cases/groups and target-independent source mappings; immutable package and receipt contracts; V01/V04–V08. Neutral package is downloadable, with no implied external success.
5. **Trade controls**: PSP legs/matching, advances, holds, partial/consolidated billing and coverage assertions; V11–V13.
6. **Automation and agent completion**: activate only fully supported financial interpretation contracts, transactional outbox, structured reads/action verification; adapter and browser matrix across all slices.

Each slice includes its own tools, catalogs, UI and verification. Do not defer all user-facing validation to the final slice. Narrow authority activation follows proof of the corresponding posting semantics.

## Rollout and Rollback

Use a positively identified disposable PostgreSQL database. Test the current Alembic chain from empty, initialize minimal accounts and generate fixtures through shared services. Verify tenant/account constraints, repeatable setup and new-model reversal/settlement history. Add tenant/account/currency/date indexes and allocation/effect/mapping indexes as planned.

No staged old/new binary compatibility or per-tenant migration activation is needed. Automatic recording still requires explicit owner authority because that is a business permission, not a migration flag. Recovery during this local development phase is rebuild/reseed of the explicitly selected disposable environment. Do not expose database reset as a normal product/agent command or run it at startup. Before onboarding real customers, establish a separate reviewed production migration/recovery policy; this local exception must not become permission to erase their history.

## Review Risks

- Existing allocation availability and supplier refund wrappers need correction before adding new consumers; tests must cover both allocation endpoints.
- All legacy posting paths must acquire the finance transaction boundary; a bypass defeats race protection.
- Per-tenant serialization is deliberately simple but limits write throughput. Benchmark representative batches before activation; finer locks require another proven design.
- Existing order-to-invoice guard rejects subsequent billing of a line; explicit evidenced partial billing must replace that guard without inventing line prices or coverage.
- Schema expansion and actual migration head require technical review before implementation; this document does not assert approval.
- Concurrent web-shell work requires an integration-path check; no alternate worktree is silently merged.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## First implemented slice — 2026-09-09

The owner explicitly approved account setup, required account IDs in existing posting paths, settlement safeguards, settings UI and clean test fixtures. This is a bounded implementation of the larger design, not completion of the 58 functional requirements.

- Persist `SubledgerAccount`, `FinanceRoleDestination` and `FinanceState` beside `LedgerEntry` in `db/core.py`; do not create the future evidence/operation/target tables before their use cases are implemented. Migration `0047_finance_accounts` follows the actual root head `0046_company_setup_demo`.
- Keep the five existing technical role keys: `accounts_receivable`, `accounts_payable`, `cash`, `sales_revenue`, `inventory`. Their display meanings are customer receivables, supplier payables, cash/bank, gross sales counterpart and gross purchase counterpart. The future conceptual `receivable`/`payable`/`gross_*` names do not require renaming these stable keys. Introduce additional roles only with their consuming slice.
- `LedgerEntry.account_id` is the only stored account authority. The Python/SQL `account` accessor derives the operational role through the tenant-scoped account relationship; it is neither a stored account code nor a legacy identity. Journal API and projection values also expose the concrete account ID and current display code. Existing role-filtered reports remain aggregate operational views.
- Confirmed creation of an ordinary or practice company initializes five reference accounts/defaults through a common private bootstrap. It creates no monetary entries. Explicit initialization remains available for an empty catalog. No country chart or tax treatment is guessed.
- Account maintenance uses shared services, typed proposal tools, owner confirmation, expected finance revision and a single transaction for the mutation and terminal proposal result. Finance mutations serialize through a tenant row. This does not claim the future economic-effect identity/outbox contract.
- Invoice-bound payment/refund commands retain the original control account even if its role default changes. Normal new use of a blocked account fails; exact reversing entries retain the original account ID. Allocation requires identical control account, party and currency; effective allocations at either endpoint consume availability.
- The migration refuses a populated ledger, performs no automatic deletion/backfill and permits an empty-only test downgrade. Temporary test databases exercise upgrade/downgrade. The active port-8080 worktree and its database are outside this cutover.
- The company settings panel reuses root web forms, tables, buttons, localization and theme styles. A separate synthetic browser harness verifies the component without touching a tenant. Integrating it into the newer active unified shell remains a separate checkout integration step.

Constitution review for this slice: PASS. No document operational status, derived monetary Fact, duplicated source/line foreign key, alternate adapter posting rule, cross-tenant relationship or automatic external effect is introduced. No critical cross-artifact finding remains for this bounded slice after recording the actual table placement, role keys, bootstrap behavior and deployment boundary here. Broader story acceptance remains open.

## Authorized active-stack integration — 2026-09-09

The owner approved continuing with integration into the actual local application, targeted rebuilding of disposable local test data and end-to-end sales/purchase verification. Preserve the newer unified shell, lot-expiry and subsequent read-performance work. Transfer only the implemented account slice. Use migration `0048_finance_accounts` after `0047_merge_demo_lot_expiry`; never apply the root migration chain to this database.

The account panel mounts in unified company settings using current `br-*` controls and theme tokens; the journal displays concrete account code/name. Existing services and proposal confirmation remain the authority. No new financial features or schema beyond the reviewed three-table slice are added.

Before local cutover, create a private backup and rehearse the combined schema on disposable PostgreSQL. Stop writers for the cutover. Rebuild only explicitly selected local business test data, preserving login/account access where practical; do not remove PostgreSQL or object-storage volumes. Seed through shared company/demo services. Verify the actual localhost application and sales/purchase invoice, partial/full payment, credit, refund and reversal paths. Retain a recoverable backup until verification completes.

Constitution review: PASS. Same account identity/evidence model, tenant-scoped services and confirmed actions; no derived Facts, financial accounting authority or external effects. Analysis: no unresolved requirements or critical integration finding; the exact target migration and UI mounting point supersede root-only limitations for this integration.

## Next bounded slice: available-credit register

Implement FR-039/FR-042 read visibility first in the active unified checkout.
Use one shared service in `services/finance/credits.py`, querying tenant-owned
LedgerEntry/Document/Party and existing effective allocations. Exclude reversal
groups and restrict origins to customer/supplier payments and credit notes with
direction-correct control sides. Return original/used/available amounts and IDs;
never net parties, currencies or accounts. Expose through the existing open-items
API using new customer-balance/supplier-balance flows and shared register UI.
No migration, new mutation or approval bypass. Rollback removes these read flows.
Constitution check: PASS (read-time derivation, shortest evidence links, tenant
scope, shared service and no schema expansion). Analysis: no critical findings;
existing credit-note filter remains unchanged; refund actions must not be offered
for payment documents until their dedicated reviewed wrapper exists.
Tests first: symmetric payments, partial allocations, refunds consuming either
endpoint, refund reversal, payment reversal, currency separation, blocked accounts,
tenant isolation, filtered totals/pagination and HTTP contract. Run backend suite,
web gates, lint and spec checks before marking the slice done.

## Accepted-adjustment implementation slice

Constitution PASS: reuse SourceRecord → dedicated Document → LedgerEntry →
SettlementAllocation. No dedicated balance/evidence table is justified: the source
retains amount, reason, actor and original evidence identity losslessly, and the
allocation is the shortest invoice relationship. Add two permitted counterpart roles
with additive migration 0049; preserve existing account identities and five-role
bootstrap defaults. Account settings can create the new roles explicitly.

Shared service `services/finance/settlement.py` previews and applies a positive
invoice-bound noncash adjustment. Owner-confirmed `finance.adjustment.accept` uses
the existing proposal table, finance revision and atomic finance dispatch, with
locks in delivery-then-finance order. All evidence/posting/allocation and executed
receipt commit together. Source/effect deduplication occurs under the finance lock.
UI uses an invoice-row action, server-computed preview and explicit confirmation;
unknown confirmation outcomes retry the same proposal. CLI/MCP use the same tool
and proposal boundary. Historical exact inverses retain their original accounts.

Tests planned before implementation: customer/supplier 100 invoice + 80 actual
payment + 20 reduction, exact entries/no cash, source chain, actor, independent
reversal, missing supplier agreement, bounds, blocked/missing accounts, tenant scope,
stale proposal, replay, duplicate source/effect, rollback and PostgreSQL serialization.
Add API and browser proof; run full backend, migration, frontend, lint/spec gates.
Downgrade refuses existing reduction-role accounts; it never erases finance history.
Analysis: no critical findings; owner has authorized symmetric accepted reductions
and limited account management. Broader matrix/tax/export work remains open.

Source identity refinement: external effect deduplication uses the immutable source
stream identity (system, type, external ID) plus the caller's stable effect reference,
not a version-specific SourceRecord ID. The exact received source version remains
in the internal acceptance payload. This prevents changed payload/reason versions
from repeating a consumed effect. Credit-note reuse checks cover the same stream.
Regression proof: `test_new_source_version_cannot_repeat_accepted_effect` failed
before this refinement and must pass before rollout.

## Guided payment and credit lifecycle implementation

Use `services/finance/settlement_flows.py` for shared context, preview and atomic
composition. Reuse `record_*_payment`, `record_*_refund`, `allocate_settlement` and
`accept_adjustment`; acquire delivery then finance locks before validation. Validate
the original revision once, then pass the current locked revision to the composed
adjustment after the payment/allocation. No externally visible intermediate commit.
Add optional action propagation to the existing supplier-refund primitive.

Use existing SourceRecord → Document → LedgerEntry/SettlementAllocation. Allocation
only uses existing credit and its evidence; the confirmed proposal records the intent.
Payment/refund internal source records hold the stated input, external evidence link
if present, actor, confirmation and time. Stable source stream/effect identity guards
new proposals as well as proposal replay. No schema migration or derived balance.

Tools: one typed mode-specific request and shared preview/execute dispatch, plus
read context for invoice or credit origin. API/CLI/MCP call these same tools. Unified
Finance adds a native dialog from invoice and available-credit rows with pending
proposal recovery, explicit review, outcome/evidence links and refreshed registers.
No independent arithmetic in the browser. Preserve existing action discovery work.

Constitution Check: all PASS (existing evidence chain; derived reads only; tenant
queries; shared services; confirmed authority; no schema expansion or external effects).
Analysis: no unresolved clarification or CRITICAL finding for this approved slice.
Broad reviewer checklist remains 40 checked/5 open; prior owner continuation applies
to bounded implementation and does not mark broad accounting/export requirements done.

Tests first: symmetric payment/difference, credit allocation/refund/reversal, stale
and concurrent revision, source replay across versions, rollback, invalid decimals,
owner and tenant boundaries, API/MCP parity. Run required full backend, lint, spec,
web/site builds and real browser proof in isolated fixtures before local image rollout.
Rollback uses previous images only when compatible; no schema/data reset is required.

## Opening-position implementation increment

Constitution Check: PASS. The owner-approved opening_scope/opening_item_detail
records are justified by repeated coverage/identity constraints, joins and due-date
reads. No running balance, financial Fact or operational status field is introduced.
Add migration 0050_opening_subledger after 0049_settlement_reduction_roles, two
tenant-scoped evidence tables and one opening_counterpart role. Preserve existing
rows and five-role automatic bootstrap; explicitly confirmed account initialization
can add the new default. Downgrade refuses populated opening evidence or accounts.

Use four dedicated opening Document kinds sharing existing control/neutral ledger
posting and settlement primitives. OpeningScope keys source namespace, party,
direction, currency and retains one snapshot/cutover/coverage mode. OpeningItem
links its Document to its scope, with stable external item key and optional original
due date. SourceRecord retains the exact stated batch/row values, original evidence
link and confirming owner. No duplicate amount authority is added to these tables.

Shared services/finance/opening.py provides context, preview, confirmed import and
coverage validation. Central normal financial posting checks historical coverage.
All financial writers acquire delivery then finance locks consistently, including
legacy writers, to serialize opening import with ordinary posting and reversal.
Add opening debts to shared open-item/aging projections and settlement contexts;
opening credits join the existing availability whitelist and refund/reuse actions.
Never derive original due dates from current terms.

Tools/API/CLI/MCP share one typed opening proposal and owner approval. Unified Finance
adds a native batch editor/review with four-direction/currency totals, stable pending
proposal recovery, unknown-date labels and result links. Existing reviewed posting
reversal previews downstream allocations; no second correction editor is introduced.

Tests first: four-direction 1000/100/800/50 fixture, residual vs original total,
unknown dates, EUR/USD separation, duplicate/snapshot/summary/old-source conflicts,
atomic rollback, owner/tenant/stale/race checks, settlement/reduction/refund/reversal,
and additive migration. Full backend, web/site, lint/spec and real browser proof
precede local rollout. Analysis: no unresolved clarification or CRITICAL finding
for this approved increment. Broader file-upload/reconciliation automation remains
explicitly future work. Existing broad checklist continuation remains authorized.

## Managed-reference implementation slice

Add one `finance_reference` table in additive migration 0051 after 0050; use the
existing finance lock/revision and confirmed proposal transaction. Codes and kinds
are immutable, names/state mutable. Reuse BusinessEvent for immutable change
evidence rather than adding a parallel history table. List/history are direct
shared service reads; no materialized projection is needed for this catalog.
Application tools, API, CLI and MCP share the same service; Company settings
uses existing controls and review confirmation. No reference is automatically
created in existing companies. Existing ledger rows and account defaults remain
untouched.

Review/analysis: Constitution Check PASS. This narrows existing FR-008/010/021/030/031
without unresolved requirements. Kind-specific identity and active resolution
prevent accidental interchange. No schema for future assignments is introduced.
Tests first: identity/validation, history, stale/replay/rollback, tenant/owner
boundaries, filtering/paging, adapters and migration, then browser verification.
Broader US2/US6 tasks remain open.

### Current UI preservation at rollout

During final runtime review, the local Web had moved to main f3d85c6 plus spec160
(page-title counts and page-local tabs) in `.claude/worktrees/page-title-counts`.
Integrate that current UI into the finance integration checkout before deployment:
retain Sales/Purchasing navigation, removal of the duplicate Workspace Facts entry,
guided rules, page titles/counts/tabs, and all finance extensions. Preserve the source
worktree untouched. Snapshot manifest and prior integration files are retained under
`/private/tmp/references-current-ui-manifest.json` and
`/private/tmp/references-ui-before-main-integration/`. Repeat frontend and browser
gates on the combined UI; do not replace port 8080 with the older shell.

## Component attribution implementation slice

Use additive migration 0052 after 0051 for the three already justified tables:
financial_component (XOR Document/Line owner, nullable exact received amounts),
component_assignment_revision (immutable basis/classification/reason/actor/action),
component_assignment_part (distinct center and exact share). All links enforce tenant
and reference kind with composite FKs. Keep source codes in original evidence; show
through the declared reader rather than duplicating them as a second authority.
Normalize a selected component only inside a confirmed assignment transaction;
select the current assignment by explicit maximum revision, never timestamp.

Read context offers 50/max200 line components, explicit summary, active reference
search, received values and current assignment. History is paged. No stored aggregate
projection: assigned/unassigned are derived in shared services. Serialize preview and
approval with delivery then finance locks. Evidence hash covers selected source values
and attribution scope; finance revision covers reference and assignment changes.
Existing confirmed action executor owns one atomic receipt.

Constitution/review/analysis PASS: bounded received-detail extraction and attribution
only; no inferred tax/net, monetary Facts, new postings, source rewrites, timers or
external effects. Tests precede implementation: source fidelity, 600/400, partial/zero/
missing, kind/tenant/owner, summary scope, immutable revisions, stale evidence/refs,
rollback/replay/concurrency and populated migration. Then shared API/CLI/MCP and a
localized native financial-detail dialog on invoice/credit rows, with review, pending
recovery, history, source links and mobile verification. Preserve the live Main/spec160
UI. Required complete backend/frontend/browser gates and backup before local rollout.

Delivery status: the bounded received-component attribution slice is implemented,
verified and deployed at 0052. See D001–D004 and verification-results.md. Automatic
source/case/account mapping, global cost reports and external handoff remain planned.

## Operational matrix delivery design

Scope review: implements the already approved operational matrix in posting-matrix.md
and fixes canonical customer-credit attribution. The eight base, two adjustment and four
opening templates live as immutable domain descriptions; actual posting services remain
the operational authority. `services/finance/accounts.py:transaction_matrix` reads the
existing tenant-scoped account/default service once and resolves descriptive legs. It
reports default configuration, never transaction readiness. No locks, writes or schema.
Expose `finance.matrix.read`, GET `/finance/matrix`, CLI `finance-matrix` and MCP
`finance_matrix`; register the shared command and tenant boundary. Company account
settings hosts a localized responsive matrix with a link to existing account controls
and refreshes after confirmed account changes. Tests compare real postings to the matrix,
exercise missing/blocked/changed defaults, isolation and read-only adapter parity, plus
a real canonical customer-credit attribution regression and browser settings checks.
Constitution Check: PASS for source authority, shortest links, tenant/service boundary,
no schema expansion, no recomputation, shared UI rules and preserved confirmation.


Browser review exposed desktop footer measurement overriding the existing mobile in-flow rule. Restore that rule below 640px in RegisterTable; verify a real canonical credit detail click at 390px plus the full shared page-chrome suite.


## Source classification implementation design

Constitution Check: PASS. One justified table `source_classification_mapping_revision` extends the approved revision design. Composite tenant FKs bind SourceSystem and kind-aware FinanceReference; unique exact scope/revision and partial current-scope index enforce one current decision. State transitions retire the previous head and append a new active/blocked revision under the shared finance lock. Existing proposals are the draft, avoiding a duplicate draft table. Revision payloads and BusinessEvent snapshots retain author/reason/action and historical destination labels.

Implement domain/DB → shared `source_mappings` services → confirmed finance tools → HTTP/CLI/MCP → localized settings and Financial detail. SourceRecord carries a system code; the read resolves its tenant-owned SourceSystem identity explicitly. No component materialization or ledger mutation during classification reads. Existing component evidence hashes remain unchanged; resolution is a separate read observation. Plan tests first for exact system/namespace/kind/code and line scope, missing/malformed declarations, blocked destinations, internal conflicts, replay/stale/concurrency, tenant/owner refusal and migration preservation. Run full backend/frontend and real browser gates before local additive rollout. Preserve concurrent FlightRecorder work.

Source revision refinement: `state` records the immutable active/blocked decision; `is_current` selects the current revision. Replacing a revision clears only its current marker, preserving the prior decision state. A partial unique index on `is_current` enforces the exact current scope.

## Finance workspace settings placement plan

Move the existing three editor components into a FinanceSettings composition. Extract
the Finance page header/tabs from its operational register body so the settings tab
never mounts register reads or actions. Extend the typed URL selection with
finance_view=settings, provide its page introduction, and pass an explicit owner
permission from the active company. Key the settings composition by tenant. Remove
financial editors from CompanySettings and retarget both catalog management links.

Constitution Check: pass. UI composition only; no domain, schema, service or financial
semantics change. Catalog destinations remain shared between agent action discovery
and web. Validate routes and action destinations first, then the complete existing
finance journey at its new location, including reload, owner confirmation and mobile.

Area navigation: extend Selection with a bounded financeSettings area and URL parameter;
compose a responsive nav/select and one editor in FinanceSettings. Add embedded display
mode to the existing account/reference/source editors so reusable standalone behavior
remains available. Restrict reference kinds by area and separate pending-review storage.
Retarget reference discovery to the Cost centers area. No financial schema/services
change. Constitution Check: PASS. Verify routing, direct visible editors, member/owner
controls, tenant resets, mobile and existing confirmed finance journeys.

Compact actions: use scoped finance-settings button styles and explicit form action
footers, retaining shared default button styles elsewhere. Reuse existing account
handlers inside a native top-layer popover so scrolling tables cannot clip it. Render
Default alongside status, not as an action. Keep a compact shared row action style.
Constitution Check: PASS; presentation-only, no backend/schema changes. Validate actual
button dimensions and placement, keyboard/popover behavior, permissions and the existing
confirmed account/reference/source journey. Rebuild only web for the local rollout.

## Delivered slice: external target mappings

Product scope is authorized by the owner's continuation after the concrete next-step
proposal. [target-mappings.md](target-mappings.md) is the bounded technical design
for three tables, shared commands/reads, evidence preview and Finance settings UI.
The observed integration head is 0053_source_classification in the active invoice-lines
worktree; recheck before adding the next additive migration. The new three-table
schema was subsequently approved after an explicit field review and the decision to
keep catalogs Finance-specific.

This slice defers accounting_profile_revision until handoff requirements consume it.
It delivers mapping resolution only, so a profile engine is not a prerequisite.
Target/reference catalogs use confirmed maintenance and audited revisions; immutable
mapping snapshots preserve reviewed reference values. Tests and execution order are
TM001–TM007; none may be checked before its required verification is green.

## Finance settings dialog refinement

User authorized the full settings usability correction, explicitly requiring the
existing application design. Presentation-only: no schema, commands, rules or money
changes. Reuse the native dialog structure of unified/SettingsPage.tsx and
unified/InvoiceCard.tsx, shared button/control tokens and list row actions.
Add a small reusable Finance dialog shell for focus restoration, busy dismissal
protection and visible error handling. Keep each existing service-backed editor and
review payload, mount it only on create/edit or recovered review. History opens
separately. Entity-specific names and concise helper text explain configuration.
Constitution: PASS; no new authority, persistence, permissions or schema.

FR-060 plan: presentation-only in AccountSettings/TransactionMatrix, reusing SettingsDialog and existing list_accounts/transaction_matrix outputs, including stable leg.role keys. No service/schema change. Add role-scoped default picker with explicit global-role/historical semantics; service confirmation/revision remains authoritative. Constitution PASS; user approved scope.

## FR-061 external accounting entry
Adapter-only change in TargetMappings.tsx: use target-list navigation instead of the permanent TargetPicker, preserve the reusable picker in mapping dialogs and preview. Store target selection through the existing session key. Hide irrelevant controls in empty lists, add contextual setup help and translate copy. No schema/domain/service change or migration. Constitution Check: all principles PASS; existing service confirmations remain authoritative. Rollback is web rebuild. Verify focused browser empty/populated navigation, all editors and real finance journey plus frontend/lint/spec gates.

## FR-062 consistent Finance settings layout
Use a small shared SettingsToolbar presentation component across AccountSettings, ReferenceSettings, SourceMappings and TargetMappings. Reuse existing tokens, card spacing and dialog footers. Keep reference kind selection separate from optional list filters, and hide unused pagination. No domain/service/schema changes. Constitution Check: PASS throughout. Tests: focused browser geometry at desktop/mobile across all areas, existing editor/recovery/permission checks, real business journey and frontend/lint/spec gates. Rollback: web rebuild.

## FR-063 empty catalogs and no-results
Adapter-only shared SettingsEmptyState with optional reset action. Recompute observed catalog presence on unfiltered reads, retain filter controls during filtered reads and clear filters on reference/target-area switches. Suppress empty account table headers. No schema/service changes; Constitution PASS. Test empty and filtered results, reset and kind switching in focused browser, retain full finance journey and frontend/lint/spec gates. Rollback by web rebuild.

PR integration: retain current main PageActionBar and inline Inspector previews. Financial detail, settlement and credit actions open from the expanded financial row; opening import is a shared page action. Verify full backend/frontend gates and the actual financial browser journey on the isolated branch before publication.
