# Implementation Plan: Global Command Palette

**Branch**: Existing checkout `234-inventory-cost-contribution`; no branch switch performed. Active Spec Kit feature is `237-global-command-palette` (setup script reports the feature name, not the actual Git branch).
**Date**: 2026-09-18 | **Spec**: [spec.md](spec.md)
**Language**: English for all repository artifacts and review evidence.
**Status**: Design complete; implementation tasks and cross-artifact analysis remain next.
**Scope review**: User accepted continuation to technical planning on 2026-09-18 after receiving the scope and next-step explanation. P1 and P2 scope is retained. No implementation or schema deployment occurred.

## Summary

Replace action-only search with one palette over existing navigation/capability metadata and a tenant-scoped shared search service. Business candidates are matched and ranked in PostgreSQL before limiting; exact targets open existing detail surfaces independently of current register pages. Existing forms, report readers, company switching and chat draft flows remain authoritative.

Use browser-local opaque references for recents/favorites. Add no business tables or fields and no background jobs. Versioned SQL normalization, edit-distance and tier support functions and justified access indexes support complete normalized/single-edit search over held fields. The main acceptance risks are the fuzzy-search workload and exact-detail navigation—not the palette's visual shell.

Design artifacts: [research](research.md), [data model](data-model.md), [search contract](contracts/search.md), [UI contract](contracts/ui.md), [quickstart](quickstart.md).

## Technical Context

**Language/Version**: Python 3.12+; existing TypeScript/React frontend; SQL/PLpgSQL for migration-owned read support.
**Primary Dependencies**: Existing SQLAlchemy 2, Alembic, PostgreSQL (CI PostgreSQL 17), Pydantic v2, FastAPI, React 19, Vite and existing browser-test harness. No new package or database extension required.
**Storage**: Existing PostgreSQL UTF8 business tables; same-browser local navigation references only.
**Testing**: PostgreSQL pytest integration/story/adapter/migration tests; shared matching fixtures; Node contract tests; Playwright keyboard, navigation, isolation and performance scenarios.
**Project Type**: Shared application core plus thin Web API and React product adapter.
**Constraints**: Tenant-scoped joins, owner-scoped private reports, lesson boundaries, opaque identity, immutable source, no browser business rules, no silent execution, UTC and Decimal preserved.
**Scale/Scope**: All spec matrix families, 100,000 searchable business records, ten concurrent users, 100ms simulated RTT; palette opening p95 <=200ms, static matching <=300ms, record matching <=1.5s after last keystroke. These are gates, not measured results.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Search returns existing identities; exact detail retains canonical provenance. No source/evidence/Reality writes. | PASS |
| Reality owns operational state | No new document statuses; optional state via bounded canonical reads; overdue/blockers use shared semantics. | PASS |
| Proven schema only | No business fields/tables; SQL functions/indexes are versioned read access support justified by FR-004/007/008 and SC-003. Browser preferences hold only references. | PASS |
| Tenant + shared service boundaries | Explicit principal/tenant service contract, tenant predicates on every joined alias, private report ownership and lesson-aware provider eligibility. Web performs no ORM reads/writes. | PASS |
| Spec/test traceability | Approved planning scope; complete FR/DR-to-test matrix below; tests first; tasks and Analyze required before code. | PASS |
| Explainable web behavior | Typed exact target opens native details/Inspector, original values and shortest provenance preserved. | PASS |
| Received values not recomputed | Search displays held values; no amount/tax/price calculations or persisted observations. | PASS |
| Smallest coherent design | Reuse catalog/forms/readers; no search server, stored search document, extension, new business detail app or preference table. Alternatives recorded in research. | PASS |

Pre-design and post-design checks both PASS for this plan. This is a design assessment, not proof that implementation checks pass. Function/index migration review remains part of normal pre-implementation technical review; no constitutional exception is requested.

## Repository Structure and Layer Changes

New paths below are planned files, not existing implementation claims.

| Layer | Paths | Planned responsibility |
|---|---|---|
| Domain | `packages/reality-core/src/reality/domain/search.py` | Result/target enums, match tiers, validation and pure reference matching |
| Storage | `packages/reality-core/src/reality/db/search.py`, `db/search_sql.py` | Complete tenant-scoped SQL selectors/ranking/continuation; versioned function definitions and install/drop helpers for migrations/tests |
| Service | `packages/reality-core/src/reality/services/global_search.py` | Principal/lesson checks, family dispatch, bounded hydration and exact target resolution |
| Shared finance reads | `services/core.py`, new `services/finance/worklists.py` | Factor canonical payment eligibility; reuse aging/outstanding rules for overdue filtering before pagination |
| Migration | `packages/reality-core/migrations/versions/<next>_global_search_support.py` | Functions and proven indexes; resolve actual head at implementation time |
| Tools/catalog | `packages/reality-core/src/reality/catalogs.py`, `packages/reality-core/config/resource_catalog.yaml` | Expose existing synonyms/launch metadata as needed; no parallel business action list or new execution tool |
| API | `packages/reality-core/src/reality/web/api.py`, `web/read_models.py` | Read-only query/resolve endpoints and finance filter parameter delegation; no new adapter-owned rules |
| Frontend data/routing | `apps/web/src/api.ts`, `unified/routing.ts`, `unified/useCompanyContext.ts` | Search contracts, exact target routes, worklist filter and complete company-reset semantics |
| Palette | `unified/ActionLauncher.tsx`, new `CommandPalette.tsx`, `commandPaletteEntries.ts`, `commandPalettePreferences.ts`, `commandPaletteTargets.ts` | Existing entry point, accessible state machine, metadata merging, local references and typed launch dispatch |
| Integration | `unified/UnifiedApp.tsx`, `Shell.tsx`, `ProfileMenu.tsx`, `apps/web/src/Auth.tsx` | Existing action targets, successful-open tracking, chat handoff, logout cleanup |
| Existing destinations | `unified/MasterDataPage.tsx`, `OrdersPage.tsx`, `FinancePage.tsx`, `ShipmentsRegister.tsx`, `InspectorRecordsPage.tsx`, `RealityInspectorPage.tsx`, `ToolCatalog.tsx`, `AnalyticsPage.tsx`, `analytics/GraphTemplates.tsx` | Page-independent detail hydration, explicit report/template/capability targets, filter visibility |
| Chat presentation | `unified/ChatPage.tsx` | Extend existing visible/removable authorized record context; preserve draft/no-send behavior |
| Presentation | `apps/web/src/localization.tsx`, `tailwind.css` | Four-language accessible palette and small-screen treatment |
| Evidence | Tests/benchmark paths in the next section; `docs/WEB_SPEC.md`, `docs/SPEC_COVERAGE_MATRIX.md`, planned `docs/features/command-palette.md` | Durable behavior contract and verification evidence; preserve concurrent unrelated edits |

Dependency order: pure domain contract -> storage queries/shared services -> catalog/tool reuse -> Web API -> frontend adapters. Existing tool implementations remain unchanged unless factoring a shared read requires a behavior-preserving import update. No scheduler/worker, company creation or synthetic-intake code is touched.

## Design

### Reality flow

Search reads authoritative Party/Item/Location, Document/SourceRecord and Reality identities. Orders/invoices/credits resolve to Document IDs; payments resolve to cash LedgerEntry IDs; shipments to Shipment IDs matched through package tracking references. Every source version remains separate. Exact selected records expose their existing provenance links; search does not traverse an arbitrary graph or fabricate business relationships.

Display only identifying metadata and optional canonical state. Do not calculate totals, balances, availability or fulfillment during matching. A result may omit unavailable state rather than invoke expensive full-tenant enrichment. Fully paid/closed/inactive records remain eligible independently of workspace defaults.

### Service and adapter flow

1. Open/focus the palette immediately; build static entries from existing navigation and unified capability/report metadata. Resolve stored references before rendering private labels.
2. Match local vocabulary immediately; debounce business search 150ms. Query separate providers with at most three in flight, scoped to tenant/principal/query generation.
3. Authorize the service; apply complete per-family predicates, rank tiers and cursor before fetching a bounded page. Hydrate labels in batches and return explicit typed targets.
4. Merge by canonical identity and ranking, using the eleven explicit visible groups in spec.md. Nonempty previews have max twelve hits overall/four per visible group; even an omitted group retains Show all when it has hidden hits. Show all pages one group with max fifty merged hits; Reports combines calculated views, templates and private reports with source lookahead. Provider boundaries grant no extra display budget. Preserve manually selected identity as results arrive.
5. On activation, revalidate record/private-target access, dismiss palette and invoke the existing native detail/form/report/chat/company path. A form open is not a mutation and a chat draft is not a send.

Static catalogs are not permission authorities. Extract/reuse shared eligibility checks where a route currently owns a policy. Explicitly preserve private lessons: only records whose existing surface is permitted may be searched/resolved; no blanket expansion of `require_tenant_surface_access` to every provider. Ordinary/practice/live-demo scope remains unchanged. Context tie-break hints confer no access.

Detailed payloads, ranking, provider/family mapping, cursor semantics and worklists are in [search.md](contracts/search.md). Exact target routes and detail adaptations are in [ui.md](contracts/ui.md).

### Data and migration impact

See [data-model.md](data-model.md). No source backfill, business-table rewrite or search index queue. Install versioned immutable normalization/single-edit functions and minimal nonunique expression indexes through Alembic before deploying the new API. Fixed normalization mappings avoid locale-dependent indexed behavior. Query and browser fixture parity is mandatory.

Index creation can lock/write-load existing tables: measure creation duration on the scale fixture, inventory equivalent indexes, and use the repository's supported Alembic deployment pattern. Do not make an immutable function's semantics change in place. Preserve the old application compatibility path throughout upgrade. The plan requires technical review of the eventual migration, not user acceptance of unknown schema expansion.

### Failure, security, and tenant behavior

Every root and joined query is tenant-scoped. Service checks membership and lesson eligibility; owner/private report reads reuse report policy. Stale cursors and incompatible scopes are rejected. Newer query generations always win, and company/user change clears all rendered results immediately. Unavailable providers remain distinct from no matches; retry does not replay a mutation.

Resolve local references before rendering, never cache business labels in persistent browser storage, and clear references on logout/session loss. Contextual action targets use a typed allowlist and current service-derived eligibility. Every real mutation retains its existing validation, confirmation, revision/idempotency and transaction rules. Search calls do not flush/commit business changes or create proposals.

Do not log raw queries, result labels or payloads. Performance evidence records query-case identifiers, counts, timings and query plans in disposable fixtures, not production business text.

## Test Strategy and Traceability

Tests are planned before implementation; add meaningful failing proofs first. New file paths are concrete targets for task generation, not commands claimed to pass today.

| Requirements | Level / planned file | Initial failure and proof |
|---|---|---|
| FR-007/008/021, DR-004 | `packages/reality-core/tests/test_global_search_matching.py`; `tests/fixtures/global_search_matching.json`; `apps/web/scripts/command-palette-ranking.test.mjs` | No shared normalization/ranking exists; prove SQL/Python/browser parity, all four languages, DE/EN synonyms, one edit/transposition, raw exact precedence and identity deduplication |
| FR-004/005/009, DR-001/002/004/005 | `packages/reality-core/tests/test_global_search.py` | No global service; seed all mapped fields/families, >50 records, closed/inactive/paid records, source versions, duplicate numbers, multi-role party, multipackage shipment, cash payment identity, unchanged source/ledger data and complete continuation |
| FR-003/011/012/014/017/019, DR-003 | `packages/reality-core/tests/test_global_search_access.py` | No authorized resolver; cross-tenant and revoked membership, lesson boundaries, private reports, forged hints/cursors, safe unavailable results, no leaked labels/counts |
| FR-004/011/012, DR-003 | `packages/reality-core/tests/test_global_search_web.py` | Endpoints absent; validate read-only POST, principal derivation, invalid inputs, provider failures, thin shared-service delegation and no autoflush/commit |
| FR-016, DR-002 | `packages/reality-core/tests/test_command_palette_worklists.py` | Overdue filter absent; parity with canonical aging/open/outbound-blocker reads before paging, both financial sides, boundary/unknown due dates and stale projection semantics |
| FR-001/002/003/005/006/009/010/011/012/015/017/018/019/020/021 | `apps/web/scripts/command-palette-browser.mjs` | Existing action-only UI fails all-family search; prove keyboard/IME/focus, 200% zoom/mobile, loading races, exact off-page routes/reload/Back, no mutation/send, report required inputs, owner gating, company reset and drafts |
| FR-013/014, DR-003 | `apps/web/scripts/command-palette-preferences.test.mjs`; same browser script | No preferences; limits, resolve-before-label, storage denial, malformed data, rename/removal, logout/cross-tab isolation, successful opens from ordinary navigation |
| FR-002/003/015/017/020 | `apps/web/scripts/command-palette-targets.test.mjs` | No typed opener; allowlist, capability/report dedup, clean route fields, source IDs and typed action prefills |
| DR-005; SC-003 | `packages/reality-core/tests/test_global_search_migration.py` | SQL functions absent; upgrade/existing rows/downgrade/re-upgrade, UTF8 preflight, index ownership and parity with metadata-created fixtures |
| SC-001–006 | `packages/reality-core/tests/test_global_search_story.py`; new `benchmarks/global_search/runner.py`; new `apps/web/scripts/command-palette-performance.mjs` | End-to-end service story, ten-user 100k mixed record workload, declared hardware and cold/warm percentile evidence plus 100ms network latency |

Regression: existing action-discovery/tool-catalog/inspector-navigation/inline-row-previews/daily-work/finance-routing/analysis-chat/snapshot/company/localization tests; corresponding browser navigation/form scripts. Backend full pytest and Ruff; frontend formatting, contract tests, build and i18n audit; spec policy; migrations; generated catalog documentation freshness and docs tests/build if catalogs change. Source-pattern tests supplement but never replace behavioral browser and PostgreSQL proofs.

Performance seed must represent every record family with at least one target beyond first-page positions, repeated/short names, duplicate references, owner-private reports, common prefix and typo cases. Freeze fixture date; use the existing guarded disposable benchmark conventions and a separate second tenant for isolation. Publish p50/p95/max, query plans, row counts, hardware/version, content digest, concurrency and cold/warm methodology. A timeout or missed budget fails acceptance; no hidden candidate caps are permitted.

## Rollout and Rollback

1. Complete task generation, consistency analysis and technical review, then test-first implementation. Leave unrelated checkout changes untouched; isolate the feature before committing implementation.
2. Apply the reviewed additive support migration through the normal deployment process; API/scheduler/worker startup never migrates.
3. Deploy matching shared-core/API/Web artifacts together. Preserve old action discovery and existing routes; new route fields are optional. No persistent business backfill.
4. Verify all-family searches, closed-record deep links, permissions, mutation/no-send boundaries and declared performance. Document results before marking done.
5. Roll back to the previous matched application release if needed. Local versioned preferences may remain inert or be cleared. Additive indexes/functions may remain until separately downgraded; if downgrading, remove only owned indexes before owned functions. No source/business rows are deleted or reinterpreted.

## Review Risks

- Complete fuzzy word predicates may be expensive at 100k records/ten users. Measure early and optimize without weakening correctness.
- Payment identity/eligibility and invoice/credit aliases can duplicate records if not canonicalized centrally.
- Off-page detail hydration, report selections and company reset affect shared routing; include Back/reload and unsaved-state regressions.
- Lesson routes and private report ownership differ from ordinary tenant membership; new discovery must not widen access.
- Blockers are broader than active holds; overdue has canonical date/aging semantics. Preserve their shared reader authority.
- Metadata-created test databases do not automatically install Alembic functions; tests must explicitly install the identical support definitions.
- Several shell/chat files already contain unrelated local work; merge edits narrowly and retain their contracts.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Planning Validation

No extension hooks are configured (`.specify/extensions.yml` absent). Setup resolved feature 235 without changing the actual Git branch. Research decisions are resolved and all Constitution rows pass. Validation passed: `python3 scripts/check_spec_policy.py`, all local artifact links, explicit test-plan coverage for all 21 FR and 5 DR identifiers, no clarification markers, and `git diff --check`. Executable feature checks remain unrun until implementation exists. The current host make/Xcode-license limitation did not affect the direct specification-policy check.

### Implementation refinement from the early performance probe

The complete initial scan timed out on 100,000 items. As reviewed in review.md, use a complete SQL regex candidate superset and `pg_trgm` GIN expression indexes over normalized human labels, alongside normalized ID/reference B-tree indexes. `db/search_indexes.py` owns migration/test setup only. The exact match function remains the authority; no sampled pool or fuzzy identifier search is introduced. PostgreSQL must provide `pg_trgm`; rollback preserves a potentially shared extension. Constitution Check: PASS (derived read-access support only, no business schema fields/tables). Correctness and actual ten-user cold/warm latency proof remain required.

### Measured HTTP admission refinement

The ten-browser read workload exposed connection-pool starvation while the async
authentication middleware synchronously acquired a database connection. Move its
existing scoped authorization block into Starlette's existing threadpool. Preserve
all response statuses and membership checks; do not change authentication policy or
raise production pool defaults. This behavior-preserving scheduling correction is
required for the spec 237 concurrency workload. Verify existing authentication and
HTTP-boundary regressions and a delayed-authorization concurrency test.

### Palette visual refinement

Reuse existing shell tokens and lucide icons. Extract a presentation-only aggregate
status component; keep provider state/retries in the existing hook. Scope CSS to the
palette so other shared buttons remain unchanged. Use a fixed viewport-bounded flex
container with independently scrolling content. Test status rendering before wiring
it, then run frontend contracts, build, localization and real-browser visual checks.
Constitution check: PASS; presentation only, no domain/schema/service changes.

### Exact destination presentation repair

Reuse a shared SelectedRecordPreview wrapper for off-page OrdersPage and
MasterDataPage details. Isolate it from register-surface child resets and scope
compact detail spacing to this wrapper; use container width for section columns.
Preserve existing InlineInspector/InspectorContent readers, actions and routing.
Regression proof covers both integrations and the wrapper's content/close behavior;
verify live order/master/Inspector destination classes and document family coverage.
Run frontend contracts, build and localization audit. Constitution Check: PASS;
no schema, API, authority, tenant boundary or vocabulary change.

Live item inspection found a selected in-page row below the visible fold. Reveal loaded InlineInspector content for order selections and loaded master detail
content by identity. Do not scroll on background refresh. Reuse compact preview
geometry for both off-page wrappers and table preview containers; their columns
follow container width rather than full browser width.

### Palette visual consistency

Use existing Lucide symbols already present in Shell and master-data navigation.
Select icons from canonical target identity, never translated labels. Scope CSS
changes to the palette; retain its dimensions, spacing grid and hit targets. Validate
with existing frontend contracts, build, localization and a live screenshot. New
behavioral tests are unnecessary for this reversible presentation-only adjustment.
Constitution Check: PASS; no service/schema/authority changes.
