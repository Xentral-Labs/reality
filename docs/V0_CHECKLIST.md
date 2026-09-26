# V0 Checklist

A box is checked only when the documented acceptance behavior has an executable green
test. A partial implementation remains unchecked and names the missing proof.

- [x] PostgreSQL bootstrap + tested complete Alembic migration chain
- [x] Tenant create/list/use/current + strict isolation tests
- [x] Party, Item, Location creation needed by demo through services and CLI
- [x] Immutable/versioned SourceRecord + Shopify fixture ingestion
- [x] Minimal Document/DocumentLine mapping
- [x] Commitment create/partial fulfillment/cancel lifecycle
- [x] Reservation create/release/consume with explicit shortage
- [x] Movement receive/ship/transfer/return/adjust + derived stock
- [x] Purchase as incoming commitment through the shared service
- [x] Explain commitment source/evidence/reality trace service
- [x] Tenant-scoped timeline including physical and financial events
- [x] Compact demo + identical `--auto` service path
- [x] Deterministic, rerun-safe normal-month scenario
- [x] Chat provider interface + deterministic dummy provider
- [x] Agent tool registry uses shared application services
- [x] Tenant-scoped materialized fulfillment projections with event checkpoints and MCP reads
- [x] Tenant-scoped envelope-encrypted secret vault for AI and future connector credentials
- [x] Mutation preview, confirmation, rejection, replay and tenant protection in Chat
- [ ] README quickstart and complete CLI surface verified
- [x] O2C service story: order → reserve → ship → invoice → partial payment → credit
- [x] P2P service story: purchase promise → partial receipts → invoice → partial payment
- [x] Current full test suite and Ruff checks green


- [ ] Unified App foundation rollout (Spec 107): implementation and technical
  verification pass (1470 backend tests, 122 frontend contracts, real-API browser
  proof, four-language/two-theme/two-viewport matrix). Owner visual acceptance
  and activation remain pending. Existing UI and Playground retirement belong
  to later increments; see `specs/139-unified-app-foundation/quickstart.md`.

- Unified App investigation increment (Spec 109): Warehouse and Exceptions
  technically verified with 1491 backend tests, 124 frontend contracts and
  operations/foundation/workspace browser gates. Rollout and retirement remain
  pending under the foundation item above; see
  `specs/141-unified-warehouse-attention/quickstart.md`.

- Unified Finance investigation (Spec 110): open items, payments and journal
  technically verified with 1491 backend tests, 125 frontend contracts and all
  unified browser gates. Rollout and retirement remain pending; see
  `specs/142-unified-finance/quickstart.md`.

- Unified Data and Sources (Spec 111): registered origins, source versions and
  exact evidence technically verified with 1493 backend tests, 126 frontend
  contracts and all unified browser gates. Rollout and retirement remain pending;
  see `specs/111-unified-data-sources/quickstart.md`.


- Unified Settings (Spec 112): account preferences, synchronized appearance and
  owner-only access/AI summaries technically verified with 1493 backend tests,
  127 frontend contracts and all unified browser gates. Rollout and retirement
  remain pending; see `specs/112-unified-settings/quickstart.md`.


- Unified Orders and Deliveries (Spec 113): customer/supplier order evidence,
  outgoing/incoming deliveries and exact-order case/Inspector traversal technically
  verified with 1496 backend tests, 128 frontend contracts and all unified browser
  gates. Facts follows in Spec114. Rollout and retirement remain separate;
  see `specs/113-unified-orders-deliveries/quickstart.md`.


- Unified Facts (Spec 114): recorded observations, scoped search/paging, exact
  subject/source traversal and original-value Inspector technically verified with
  1499 backend tests, 129 frontend contracts and all unified browser gates.
  Both explicitly missing Workspaces are now present. Rollout and legacy/Playground
  retirement remain separate; see `specs/114-unified-facts/quickstart.md`.


- Unified ERP Table Standard (Spec 115): all16 scoped register variants use shared
  density, sticky columns/headers, persistent layouts and server sort/page-size
  controls. Technically verified with1512 backend tests,131 frontend contracts,
  all unified browser journeys and authenticated sample checks. Overall rollout and
  retirement remain pending; see `specs/115-unified-table-standard/quickstart.md`.

- Unified receipt and reservation release (Spec 116): supplier receipt and full
  active-reservation release are available from records, the global launcher and
  matching company Chat/Decisions reviews. Verified with 1522 backend tests,
  131 frontend contracts, four-language review layouts, existing operational
  browser journeys and authenticated sample API reviews. No stock effects were
  committed by the sample preview review check. Rollout and retirement remain
  pending; see `specs/116-unified-receipt-release/quickstart.md`.

- Unified delivery holds (Spec 117): delivery-specific hold/release, reason and
  original note, and distinct customer-wide blockers are available through cases,
  the global launcher and matching Chat/Decisions reviews. Verified with 1530
  backend tests, 131 frontend contracts, four-language responsive browser checks,
  existing delivery/receipt/release regression journeys and authenticated sample
  proposal/reload/rejection. No hold was applied by the live preview check.
  Party/document hold editing and overall rollout/retirement remain separate;
  see `specs/117-unified-delivery-holds/quickstart.md`.

- Unified movement corrections (Spec 118): movement reversal and quantity replacement
  are available from Warehouse, Actions and matching Chat/Decisions reviews, with
  reason, exact projected effects, explicit confirmation and attributable recovery.
  Verified with 1543 backend tests, 131 frontend contracts, localized responsive
  correction checks and existing delivery/receipt/release/hold browser journeys.
  Shared login and real movement form reads pass; no test business changes were
  made in the shared database. Broader corrections, rollout and retirement remain
  separate; see `specs/118-unified-movement-corrections/quickstart.md`.

- Unified order entry (Spec 119): multi-line sales/purchase agreements are available
  through Orders, Actions and matching Chat/Decisions reviews, with explicit stated
  totals, current-reference confirmation, source/line metadata preservation and
  exact creation receipts. Recorded orders link to each delivery's work area.
  Verified with 1559 backend tests, 131 frontend contracts, four-language responsive
  browser proof, existing action journeys and shared login/form reads. No test order
  was recorded in the shared database. Financial entry, rollout and retirement remain
  separate; see `specs/119-unified-order-entry/quickstart.md`.

- Unified invoice entry (Spec 120): customer/supplier invoices can be entered through Finance
  and Actions, with shared Chat/Decisions review, stated quantities/amounts, exact attributed
  financial receipts and recovery. Existing one-line/no-repeat billing limits are explicit.
  Verified with 1,572 core tests, 131 frontend contracts, localized responsive invoice checks,
  existing action/finance browser journeys and shared login/form reads. No test invoice was
  recorded in the shared database. Payment/credit migration and overall retirement remain
  separate; see `specs/120-unified-invoice-entry/quickstart.md`.


- Unified payment entry (Spec 121): customer/supplier payments against one selected invoice,
  including partial settlement, are available through Finance, Actions and shared Chat/Decisions
  review. Confirmation records the stated amount unchanged, with exact allocation proof and
  response-loss recovery. Verified with 1,593 backend tests, 131 frontend contracts, localized
  responsive payment checks, prior invoice/order/finance journeys and shared login/form reads.
  No test payment was recorded in the shared database. Existing-payment allocation, credits,
  refunds and overall rollout/retirement remain separate; see
  `specs/121-unified-payment-entry/quickstart.md`.


- Multi-position invoices (Spec 122): one customer/supplier invoice now supports multiple
  selected positions of the same order, with independently stated quantities, line amounts
  and header total. Shared review, exact all-line receipts and recovery retain legacy
  single-position compatibility. Verified with 1,608 backend tests, 131 frontend contracts,
  localized invoice layouts and payment/finance browser regressions. Shared form reads passed
  without test financial mutations. Further partial billing and financial corrections remain
  separate; see `specs/122-multi-position-invoices/quickstart.md`.


- Unified financial reversal (Spec 123): Finance, Actions and matching Chat/Decisions use one
  reason/review/confirmation flow for complete posting-group reversal. Exact inverse entries,
  allocation activity and invoice/payment before/after effects are inspectable; attributed
  recovery preserves history. Verified with 1,623 backend tests, 131 frontend contracts,
  localized reversal views and prior invoice/payment/finance browser journeys. Shared login
  and the actual empty choice state pass without test financial writes. Credit/refund/rebilling
  and overall retirement remain separate; see `specs/123-unified-financial-reversal/quickstart.md`.


- Partial invoicing and rebilling (Spec 124): customer/supplier invoices can consume partial
  quantities and later bill the remainder. Complete invoice reversal releases quantity without
  deleting history. Shared forms/reviews expose remaining quantities and invoice evidence;
  stale and concurrent writers cannot oversubscribe. Verified with 1,633 backend tests,
  131 frontend contracts, four-language invoice/reversal layouts and payment/Finance browser
  regressions. Shared users/tenants and actual form reads pass without financial test writes.
  See `specs/124-partial-invoicing-rebilling/quickstart.md`.


- Invoice-linked customer credits (Spec 125): direct invoice-row or Actions entry, selected
  multiple positions/partial quantities, independently stated credit values and explicit
  netting share the Chat/Decisions review and exact recovery flow. Inspector follows
  credit→invoice→order; financial credit does not move goods or issue a refund. Verified with
  1,654 backend tests, 131 frontend contracts, four-language responsive credit views and
  adjacent financial browser flows. Shared users/tenants and empty invoice choices pass
  without financial test writes. See `specs/125-unified-invoice-credit/quickstart.md`.


- Customer refunds from open credits (Spec 126): Finance adds Customer credits with
  selected-row refund entry; Actions, Chat and Decisions share partial refund review,
  explicit confirmation and exact recovery. The common allocation guard prevents credit
  reuse across refunds and netting. Historical refund proof survives reversal; current
  balances remain derived. Verified with 1,687 backend tests, 131 frontend contracts,
  localized refund views and adjacent payment/credit/reversal/Finance browser journeys.
  Shared login, five tenants and empty credit choices pass without financial test writes.
  See `specs/126-unified-customer-refund/quickstart.md`.


- Complete unified business journey (Spec 127): real ordinary-owner browser run against
  disposable migrated PostgreSQL completed order, reservation, partial shipment/invoice,
  payment, credit, partial refund and refund reversal. Persisted receipts, remaining balances
  and shortest evidence links verified; shared company data untouched. Scoped reversal
  wording fixed for credits/refunds. Verified with 1,689 backend tests, 131 UI
  contracts, the real browser journey and localized reversal regression. See
  `specs/127-unified-business-journey/quickstart.md`. This proves the bounded journey,
  not every legacy capability or readiness to remove old navigation.


## Unified company and member administration — Spec 128

- [x] Company identity and reviewed empty creation in unified Settings, including no-company entry; bootstrap chooses returned ID and duplicate names are distinguished.
- [x] Owner invitation/resend/revoke/member removal through existing services with confirmation, queued-versus-delivered distinction, unknown-result checking and ordinary-member restrictions.
- [x] Invitation acceptance enters exact returned company; company changes discard drafts. All four languages and responsive review layouts verified.
- [x] Validation: 1689 backend passed / 7 existing skips; 131 UI contracts, 100 i18n tests, 1689 audited keys per language, build/format/lint/spec/diff checks; new company-access browser and existing 48-layout settings browser passed. Browser writes intercepted; no shared data or real mail touched.
- Company details remain read-only. Rename, lifecycle/deletion, source/provider setup and old-app/Playground retirement remain separate work.

## Reviewed new-item CSV import — Spec 129

- [x] Unified Data & sources provides bounded UTF-8 CSV upload, explicit column/default mapping, full review and confirmation for new items only; original attachment and exact item/source links remain available.
- [x] Whole-batch validation and rollback, tenant authorization, concurrent SKU conflict checks, proposal replay and explicit unknown-result recovery verified. Legacy item-file atomicity/replay/retry regressions pass.
- [x] Real isolated browser upload/confirm/download/recovery and cancellation passed with ordinary-member login; four-language responsive layouts and item Inspector verified. No shared company data imported.
- [x] Validation: 1705 backend passed / 7 existing skips; 24 focused tests, real browser runner and existing 48-layout sources browser passed; 131 UI contracts, 100 i18n tests, 1723 audited keys per language, build/format/lint/spec/diff checks passed.
- Other CSV profiles, source/provider configuration and legacy app/Playground retirement remain separate work. B1 is only partially covered.

## Unified source definition management — Spec 130

- [x] Source registration and existing source/type configuration live in Data & sources, with normalized reviews and explicit registry-only state semantics.
- [x] Unknown responses block writes across reload until explicit current-state checking; failed reads retain the block. Single-flight and in-flight company switch verified. Matching code is not claimed as a recovered action receipt.
- [x] Contextual source IDs, declared types, interpreter availability, empty/missing/error states and 25-type paging verified in four languages and responsive dark views.
- [x] Validation: 1705 backend passed / 7 existing skips; source configuration browser, existing 48-layout sources browser and actual isolated item CSV browser passed; 131 UI contracts, 100 i18n tests, 1746 audited keys per language, build/format/lint/spec/diff checks passed.
- Backend unchanged. Source configuration tests intercept writes; real item CSV regression uses disposable PostgreSQL. No shared company records changed. Connector transport/templates, new declared-type creation and broader legacy retirement remain open.

## Unified AI setup and MCP access — Spec 131

- [x] New Settings owns reviewed managed/company-Anthropic credential setup with explicit retain/replace/revoke effects. Other stored provider details remain readable with current runtime limitations; legacy administration link removed from this flow.
- [x] Explicit MCP tool selection starts empty; read/propose/confirm scopes are reviewed. Existing wildcard scopes remain visible. One-time secrets, copy/manual fallback, exact-ID revoke and bounded token/tool displays verified.
- [x] Secret-free unresolved markers, explicit current-state recovery, no automatic replay, generic secret-safe errors, owner gating and in-flight company switching verified.
- [x] Validation: 1705 backend passed / 7 existing skips; new 16-layout AI/MCP browser and existing 48-layout settings browser passed; 131 UI contracts, 100 i18n tests, 1788 audited keys per language, build/format/lint/spec/diff checks passed.
- No backend change, real provider request or shared credential/token mutation. Actual additional-provider runtime support and overall legacy/Playground retirement remain separate work.

## Unified opening stock — Spec 132

- [x] Warehouse/launcher and matching Chat/Decisions share reviewed untracked opening-stock entry; current physical stock plus entered quantity is explicit, with optional occurrence time and unchanged reservations.
- [x] Existing movement tool, exact item/location/quantity guards, tenant serialization, stale-review rejection, mutual unresolved-pool blocking and request replay preserve stock authority without fabricated source/documents.
- [x] Attributed movement/event/output proof, committed-result recovery without replay, historical correction proof, Inspector links and existing Warehouse correction access are verified.
- [x] Validation: 26 focused opening tests; complete backend run had 1730 passed / 7 existing skips and one documentation wording failure, corrected and followed by all 8 repository-layout tests passing. No backend source/test changes followed that complete run. New 16-layout opening browser, 16-layout correction browser and 64-layout workspace browser passed; 131 web contracts, 100 localization tests, 1808 audited keys per language, build/format/lint/spec/diff checks passed. See Spec 132 quickstart for exact evidence.
- [x] Local API updated with existing shared users/tenants; no shared company stock was changed during tests. General adjustments, tracked opening workflows and legacy/practice retirement remain separate work.

## Unified customer-wide delivery holds — Spec 133

- [x] Customer delivery, selected customer master data, Actions and matching Chat/Decisions share reviewed customer-wide placement/release, distinct from individual delivery holds.
- [x] Current/future customer shipments are blocked while new reservations remain allowed; release preserves individual holds, stock, reservation quantities and money. Review binds customer identity and exact active hold set.
- [x] Canonical tools attribute exact events and receipts; tenant/state revalidation, same-customer unresolved shipment/correction overlap, replay and historic release/rehold recovery are verified without new schema.
- [x] Validation: 1750 backend passed / 7 existing skips; 29 focused tests; new 32-layout customer-hold browser and existing hold/opening/delivery browser suites passed. 131 web contracts, 100 localization tests, 1826 audited keys per language, build/format/lint/spec/diff checks passed. Local API updated; no shared business test mutations.
- [x] Document-wide hold controls and legacy/practice retirement remain outside this increment; exact scope and evidence are recorded in Spec 133 quickstart.


## Unified activity drawer — Spec 134

- [x] Header Activity opens read-only company history from any unified workspace, preserving route and unfinished inputs; native modal dismissal/focus and company-change invalidation are verified.
- [x] Search, four occurrence-time windows, historical attention filtering, explicit refresh and recording-sequence paging use the existing timeline service. Split correlations, duplicate IDs, failed older pages and stale responses are covered without process-total/current-status claims.
- [x] Business titles and labels are localized; original context/payload remains escaped and intact. Event and supported subject Inspector links, nested dismissal and 16 localized responsive light/dark layouts pass.
- [x] Validation: 1750 backend passed / 7 existing skips; new Activity and existing unified application/delivery browser suites passed; 131 frontend contracts, 100 localization tests, 1869 audited keys per language, build/format/lint/spec/diff checks passed. No shared business data mutations or API changes.
- [x] C1 Technical Explorer and overall legacy/practice retirement remain separate work; bounded scope and exact verification are recorded in Spec 134 quickstart.


## Compact shell and persistent chat — Spec 135

- [x] Owner-requested compact sidebar and sticky 56px header; toggleable right chat retains drafts across hiding/workspace navigation and resets on company change.
- [x] Delivery discussion and copilot links use the common dock; Analytics with Reports is immediately before Settings in primary navigation. Temporary migration links remain separate.
- [x] New 48-layout browser, existing application/delivery and 16-layout activity browser passed; 131 contracts, 100 localization tests, 1872 audited keys per language, build/format/lint/spec/diff checks passed. No backend changes or shared business mutations.
- [x] Early UI sequencing is explicitly recorded; functional closure and final retirement remain open.


## Reference-style chat composer — Spec 136

- [x] One compact conversation header with history/new-chat icons, flat messages/Markdown tables and one composer with paperclip, microphone and send arrow; shared context and proposal review remain.
- [x] Local text-file limits and unchanged 4,000-character message boundary are enforced without truncation. Dictation appends a draft, stops on hide/session teardown/send and exposes unavailable-browser/error states.
- [x] Composer interaction proof, 48 localized shell layouts, existing full application/delivery and 16-layout Activity suites passed. 131 contracts, 100 localization tests, 1890 audited keys per language, build/format/lint/spec/diff checks passed. Browser speech is simulated; no physical microphone/provider success claim or shared business mutation.
- [x] Backend unchanged; Spec 134 full-suite baseline remains. Binary attachments, functional closure and legacy/practice retirement remain outside this increment.

- [x] Spec 137: compact operational/master-data workbenches, consistent toolbar actions, shared selection/CSV/pagination footer; table/workspace/order/finance/facts browsers, contracts/build/localization/format/spec checks green. Bulk mutations remain outside scope.


## Reality Inspector — Spec 138

- [x] Technical workspace with existing scoped record/graph, rule lifecycle, exception/command/action/projection catalogs and history. Existing supported Web forms retain review boundaries.
- [x] Inspector and shared shell/table browser suites, 132 contracts, localization/build/format/lint/spec checks passed. No live business mutation or new backend verification claim; see Spec 138 quickstart. Legacy retirement remains separate.

- [x] Spec 135 FR-008: removed all twelve audited unified-to-legacy exits. Unsupported proposals remain visible, practice companies retain the operations guard with live-company recovery, and role-less receipt links stay in Inspector. 133 contracts, localization/build/format/spec checks and shell/application/delivery browser gates passed. Legacy applications/data remain intact.

- [x] Spec 138 FR-001/007/008: dedicated four-part Inspector navigation and context-first record/graph/detail explorer; grouped existing catalogs and lifecycle preserved. Inspector/shell browsers, 133 contracts, build/localization/format/spec checks passed. No live business mutation.

- [x] Spec 137 FR-005: reference-style title/tabs and table toolbar, grouped existing page actions, shared filter/column/density row and compact empty guidance. Five register browser suites, 133 contracts, build/localization/format/spec gates passed.

- [x] Spec 137 FR-006: actual global-header register title/tabs and compact filter/density/column chips; header ancestry, native controls, localized table/shell/order/workspace browsers, build/contracts/localization/format/spec checks passed.

- [x] Specs 137 FR-007 and 138 FR-009/010: shared Inspector/Company header, visible rule-version actions and explanations, administrator permission parity, readable editors and tenant-scoped rule-state filtering. 1790 backend tests passed (7 skips), 133 frontend contracts, localized Inspector/settings/sources browsers, build/localization/format/lint/spec checks passed.

## Local company setup and scheduling integration (specs 146/147)

- [x] Shared creation and automatic live-demo source setup are available in the unified
  app; company cards contain their controls and show truthful type/source state.
- [x] Local port 8080 uses matching API/web/background code and the additive merged
  migration; existing data preservation and regression checks are recorded in spec
  146 quickstart.md and docs/LOCAL_STACK.md. This does not assert remote deployment.

## Physical Shipments and Tracking — Spec 173

- [x] Customer/supplier deliveries and both return directions use Shipment → Package → effective
  Movement as the shortest physical trace. Commitments remain promises; carrier events never move
  stock or become mutable delivery status.
- [x] Carrier/tracking, append-only observations, explicit supersession, lossless SourceRecord
  evidence, derived quantities/times/discrepancies and Shipment/Package Inspector views are
  tenant-scoped and available through shared Web, CLI, HTTP, MCP and Chat capabilities.
- [x] Five state-bound mutation workflows require review and explicit confirmation and preserve
  atomicity, stale-state refusal, replay and lost-response reconciliation. Existing un-packaged
  Movements remain valid; migration 0056 performs no historical backfill.
- [x] Validation: 2,285 backend tests passed / 9 skips; 83 focused Shipment/return/migration/
  correction tests and 46 stale/replay regressions passed; 123 frontend contracts, 1546/1546
  localization keys per language, build/format/lint/spec/diff gates and the five-form responsive
  four-locale Chromium matrix passed. No shared company data or active port-8080 stack was changed.

## Chat agent decisions — Spec 274

- [x] Ordinary product Chat can prepare and separately confirm or reject an exact stored proposal through the shared application boundary; proposing alone never mutates business state, while protected owner/person checks and read-only Playground policy remain unchanged.
- [x] Chat-settled decisions are durably and truthfully attributed to the Chat agent, retain tenant, stale-review, replay and operation-specific safeguards, and remain traceable through the Decision Trail.
- [x] Validation: complete serial PostgreSQL backend suite passed with 4,388 tests and 10 skips; focused Chat, attribution, migration and frontend suites, Ruff, spec policy, generated catalog, four-language audit, production Web build and diff checks passed. See Spec 274 quickstart for exact evidence.
