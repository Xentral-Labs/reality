# Plan
## Constitution Check
PASS all principles: no schema, domain rules or direct persistence; only existing tenant-scoped reads and application endpoints. Graph edges are received Inspector links. Shared ActionCards preserve preview and confirmation.
## Design
Add inspector route/tab serialization, Shell entry and RealityInspectorPage. Reuse FactsPage, ExceptionCatalog, existing Inspector and activity timeline. New ObjectGraph and RuleWorkbench components remain tenant-keyed. Catalog search uses applicationReference; explicit action mapping reuses supported DeliveryAction values. Rules keep the existing gap/revision lifecycle and typed rule draft contracts. No legacy shell/CSS import.
## Tests
Write isolated browser fixture before implementation; test tabs/deep links, actual graph edge labels, catalogs and form entry, rule review-before-write/simulation/activation and errors. Run frontend contracts, i18n, build, formatting, spec gates and local browser. Existing backend baseline is applicable because no service changes.
## Rollback
Remove route/page/components. No data migration; created rules remain in existing services and legacy-compatible management.

## Navigation refinement
Owner approved moving the entry to Company before Settings, labelled Technology & system (German: Technik & System). Keep the Inspector title and URL. Constitution Check: PASS; adapter navigation/copy only. Verify section, ordering and active link using the existing Inspector browser fixture, plus build/localization checks.

## Context-first structure
Constitution PASS. Owner approved four Inspector sidebar destinations between Analytics and Company. Share section metadata between Shell and page. Preserve inspector_view URLs; page shows only tabs for the current group. Add ContextExplorer using existing explorer and inspector reads, with record picker, semantic guide, actual metrics and ObjectGraph. Optional graph navigation callback keeps the explanation synchronized with selected nodes. Existing global chat/service boundaries unchanged. Test group hierarchy, old tab links, real fixture record context/graph and existing lifecycle through browser; build/contracts/i18n/format/spec checks.

FR-009: presentation-only correction in UnifiedApp and RulesWorkbench. Reuse authenticated platform-admin metadata and existing role, handlers and confirmation boundaries. No permission grant, backend change or destructive deletion. Constitution PASS. Extend Inspector browser to prove admin without owner membership, member denial, visible version actions, draft focus and single-page pagination; run existing rule lifecycle and shared header checks.

FR-010: Add optional validated rule_status to list_gaps and its HTTP adapter, using a tenant-scoped correlated EXISTS before count/pagination. Return grouped version states for listed questions only. Client sends the filter and filters selected versions without alternative business rules. No schema changes; Constitution PASS. Plan PostgreSQL test for mixed lifecycle/version states, pagination, unknown state and cross-tenant exclusion; Inspector browser tests query/filter/empty/reset.

FR-011: Add embedded presentation to existing ExceptionCatalog and ActivityDrawer; reuse fetch/error/filter/cursor behavior and RegisterTable for inline history. Inspector mounts embedded surfaces directly. No schema/service changes. Constitution PASS. Verify Inspector direct-tab table/catalog rendering and no initial dialog, plus existing activity drawer browser, build/contracts/localization/spec checks. Runtime application-reference 500 was traced to an old process with new on-disk catalogs; current process returns 200 after restart.

History uses RegisterTable cursorView metadata for column widths and isolated preferences; page-size and server-sort controls are omitted because timeline uses a recorded-sequence cursor and fixed ordering. Its existing Load older control remains authoritative.

FR-012: Reuse RegisterWorkbench/Toolbar/Table and the existing RulesWorkbench handlers; introduce an explicit editor-open state and native dialog. All list controls retain service-owned filtering/pagination. Close is blocked during in-flight work; unknown outcome persists outside the dialog until reload. Reset transient form fields when beginning a new edit. Constitution PASS, no backend/schema changes. Extend Inspector browser for table row entry, new modal, Escape/focus, existing draft/review lifecycle, uncertainty and member access; run contracts/build/i18n/format/spec checks.

FR-013: Scope explicitly approved by the user's uniform-pattern request. Constitution PASS;
no schema, new business rules, authorization or persisted derived state. Add shared
InspectorCatalog/InspectorDisclosure presentation, reuse register toolbar, and apply to
fixed catalogs and record collections. Keep overview/graph specialized and table-backed
facts/rules/history intact. Gate application-reference reads by consuming tabs. Deduplicate
evidence parsing within each catalog validation call only, with no stale process cache.
Plan tests first: browser pattern/search/empty/actions assertions and catalog parsing/error
regression, followed by frontend gates and backend catalog tests. Rollback is adapter and
loader implementation only; no migration. No unresolved scope questions.

FR-014: User approved autocomplete on the graph ID field. Constitution PASS. Extend the
existing bounded explorer read with an optional allowlisted record kind; only explicit
kind requests include Fact/DocumentLine and the existing payment-as-ledger-entry Inspector
alias. Preserve unfiltered explorer shape and tenant-scoped SQL search before limit10.
Use a debounced accessible combobox with stale-response cancellation and existing graph
entry. Tests: scoped kind/name/ID search, unsupported kind, bound and foreign exclusion;
browser keyboard/click/manual-ID/type reset and stale response. No schema or migration.

FR-013 chrome refinement: remove only embedded Facts help and the Inspector's standalone
predicate-count preamble. Reference metadata is now needed only by commands/views. Assert
both absent on their Inspector tabs; no read or rule semantics change. Constitution PASS.

FR-015: User approved the proposed automatic graph and category entries. Constitution PASS:
presentation-only candidate selection using existing scoped typed explorer and Inspector
reads, no schema or stored derived state. Extract graph form/start selection into
RecordGraphPage; preserve explicit roots from Facts/records. Sequential category fallback,
up to three Inspector reads for the first populated category, distinct returned links for
ranking, and cancellation guards. Existing ObjectGraph remains authoritative for edges.
Tests first: auto linked seed, category switch, explicit root preservation, manual selection
winning a delayed lookup, empty tenant, retry; desktop/mobile and existing graph workflows.
Run browser/build/contracts/i18n/spec/diff gates. Backend unchanged; prior backend evidence
remains applicable. Rollback removes adapter entry selection only.

FR-016: Approved by the user's graph-first Overview request. Constitution PASS. Extract
shared bounded graph seed loader and category navigation from RecordGraphPage. ContextExplorer
uses them for initial root/viewed record and retains current graph/detail reads. Move graph
above search and collapse the conceptual guide below it. Manual search/select cancels seeds.
Extend browser to prove automatic overview graph+detail, their order ahead of record search,
category switching and linked-node detail navigation; run existing frontend gates. No backend
change or migration. Preserve manual graph roots when moving between Inspector tabs.

FR-017: Owner explicitly requested modal projection results matching action entry behavior.
Constitution PASS. Extract ProjectionDataDialog with native dialog and tenant/name-keyed
useRead. Reuse existing projection endpoint and read-only RegisterTable; no backend, business
mutation, schema or data substitution. Retain bounded raw JSON behind disclosure. Browser
proofs: immediate dialog, actual fixture cells, error/retry, empty, Escape/focus and reopen.
Run Inspector/browser, build/contracts/i18n/format/spec gates; backend unchanged.

FR-017 follow-up: Replace route/drawer dispatch with explicit existing read adapters for register views. Preserve modal lifetime and tenant scope. Constitution Check: PASS; no service/schema changes. Verify a routed register and a projection-backed view in browser, including unchanged URL.

FR-018: Approved two-column catalog layout with local information disclosures. Constitution Check PASS; presentation only. Verify keyboard/click help, desktop/mobile geometry and existing modal behavior in the browser.

FR-018 extension approved: Reuse the same heading and column pattern for actions/commands; include their help and layout in browser checks.

FR-018 help refinement uses a shared accessible tooltip with hover/focus/touch support, Escape dismissal and translated ERP examples; browser verifies hover, keyboard and touch-like click.

FR-019 approved: Reuse configured docs origin and checked-in catalog pages; use an explicit route allowlist and action target metadata for application links. Constitution Check PASS. Browser verifies documentation href/target, explicit app navigation, and unchanged data-modal behavior.

FR-019 navigation extension: Add a native external anchor to Company navigation using existing Documentation translation and docs origin. Constitution Check PASS; no data or permission changes. Verify production build and anchor attributes/order.

FR-020: Review approved progressive explanation using existing validated metadata. Add only repository-relative source path/function to service contracts (no file content or line claim). Shared entry component renders known metadata, relationships, labelled examples, contracts and optional raw JSON. Constitution Check PASS; no schema/business logic change. First extend reference HTTP regression to validate source metadata against repository files, then implement; verify browser structured content and collapsed technical details plus existing actions/dialogs, backend reference tests, build/locales.

FR-021 approved: Add an allowlisted source reader at the catalog adapter boundary, resolving kind/key against validated catalog and static register adapter mapping. Read function source only on request; keep it out of the initial catalog payload. Constitution Check PASS. First add HTTP tests for all four kinds, unknown keys/kinds, actual source and direct view mapping; then modal with selector and error/lifetime browser regressions. No schema or business mutations.

FR-022 approved: Shared entry component receives an actions slot; remove repeated generic introductory copy when entry description exists, simplify titles and group technical controls below a divider. Constitution Check PASS; presentation only. Verify existing Inspector flows, action-row order and desktop/mobile screenshots, build/locales.

FR-023 approved: Reuse RegisterWorkbench/Toolbar/Actions and existing register tables. Systems use cursorView presentation because its API does not support table sorting/page size. Convert existing source/import panel roots to native dialogs, retaining state/recovery logic and disabled Close while busy. Constitution Check PASS; no backend/schema changes. Verify existing source-configuration and CSV import browser stories plus toolbar/paging/modal checks, build/locales/contracts.

FR-023 spacing review: Shared inset wrapper for all three tables; verify the table begins
inside the surface rather than touching its border. No semantic impact.

### FR-024 implementation plan
Reuse api.timeline(hours=0, before_sequence) and existing Inspector. Add FlightRecorder component keyed by tenant at Overview. Single-flight cursor loading, effect cleanup and IntersectionObserver sentinel with manual button. Present explicit source → recorded event → subject relationships, plus causation links only when held. Existing Record graph stays unchanged. Constitution: PASS; read-only adapter, shared tenant service, no schema/authority changes. Verify browser fixtures for paging/errors/isolation/links/responsive, production build and localization/contracts.

### FR-025 plan
Update Shell and DataSourcesPage presentation labels and four-language dictionaries; retain existing URLs and source-registration guidance. No business/schema change. Constitution PASS. Verify production build, locale audit and existing frontend contracts; adjust affected browser label selectors.

### FR-026 plan
Add pure flightRecorderGraph.ts for deduplicated nodes, explicit reference edges and deterministic lane/time layout, with Node tests before implementation. Render accessible HTML node buttons over SVG edges inside a horizontal/vertical scroll container, sticky lane labels and time header. Reuse timeline reads and Inspector; no dependency/backend/schema change. Position by ascending recorded sequence and restore scrollLeft by added width after older fetches. Selection uses connected components of held edges only. Constitution PASS: presentation-only references, tenant-keyed existing service, no new authority or inferred relationships. Verify graph model tests, updated paging/selection/dialog/mobile browser tests, build, locales, frontend contracts and spec policy.

### FR-027 plan
Add tenant-scoped services/inspector_register.py read service with static model/field allowlists and deterministic family-then-ID pagination over bounded summary rows. Expose GET inspector-records through authenticated tenant router. Do not return source payloads in list rows; Inspector remains the payload boundary. Add InspectorRecordsPage with shared register toolbar, direct kind filter, display controls, pager and existing Inspector/graph actions. Preserve FactsPage under the Fact filter and operational facts route. Store inspector_record_kind in selection URL. Constitution PASS; no business calculations/schema/write path. Tests: service/API total paging/search/allowlist/isolation, browser filter/record/graph/reload and existing facts regressions, build/locales/contracts.

## FR-029 implementation plan
Use inspectorSections.ts as the ordered source for sidebar destinations and tab labels. Canonicalize the legacy records tab to facts at the presentation boundary. Retain the paginated InspectorRecordsPage and put the existing grouped technical preview in a lazy disclosure below it; no second primary register or removed fields. Change wording in contextual links and Timeline heading, plus DE/NL/ES catalogs. Tests first: canonical section ownership, one primary record tab, default Actions history, exact tab order and legacy URL/filter preservation. Then web contracts, format/i18n/build, browser navigation and local web-only rollout. Constitution: all PASS; no new authority, database changes, domain rules or mutation paths. Rollback is the scoped frontend commit.

Final terminology uses Facts as the broad navigation umbrella, with Additional facts for the specific Fact type filter. Preserve type IDs and the Source → Evidence → Reality authority boundaries; document this user-facing distinction in the concepts guide.

FR-029 owner refinement: move the existing views tab into Facts after facts, retaining its route and derived-result explanation. Update the shared section-order regression; verify web gates and local navigation. No content, read or business-rule changes; Constitution PASS, no open clarification.
