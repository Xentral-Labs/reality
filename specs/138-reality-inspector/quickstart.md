# Verification and review

Open http://localhost:5177/app/inspector and select a company. Reality Inspector is a dedicated group between Analytics and Company, with four destinations: Understand context, Facts & origins, Rules & insights, and Actions & history.

## Acceptance
- Search Facts or Reality records, open a real record graph, follow a returned link and open its Inspector details. Graph shows up to 20 direct links; it is not a complete company graph.
- Inspect documented rule questions and their versions. Owners can create a question, add context, decide on Fact interpretation, prepare a JSON draft, simulate and explicitly confirm activation or disabling. Member controls are read-only. Service validation remains authoritative.
- Inspect all catalog commands/actions and projection/view definitions. Explicitly mapped Web actions open shared reviewed forms; other commands display their supported adapters. Projection display is bounded to 100 returned rows and does not claim to be a full export.
- Open sources and the scoped activity history. Switch company to clear transient context.

## Evidence
- Inspector browser: graph navigation, native singular explorer collection names, route reload, catalogs, existing action form, projection data, rule creation/draft/simulation/activation, review boundaries, ambiguous 503 response without resubmission, tenant/member isolation and 16 localized light/dark mobile/desktop layouts.
- Shared shell browser: 48 layouts; shared table browser: 24 layouts and density, preference, pagination and sticky-column behavior.
- 132 frontend contracts, localization audit (1938 keys in each of four languages), TypeScript/Vite build, changed-file formatting, Ruff, spec policy and diff whitespace checks passed.
- Browser mutations use isolated fixtures; no live company rule was created or activated for acceptance. No backend changes; the previous Spec 134 full backend baseline remains applicable (1750 passed, 7 skipped), not rerun here.

## Review
No new schema or business rule implementation. Reads and writes use existing application APIs. Rules are discovered through paginated documented questions and edited as technical JSON. Unsupported Web commands remain definitions; legacy retirement is outside this increment.

Navigation refinement verified: Company section, immediately-before-Settings order, active link and unchanged title/route. Inspector browser including 16 localized layouts, build, 1939-key localization audit, formatting, spec policy and diff checks passed.

Context-first refinement (FR-001/007/008): four sidebar destinations and group-local tabs preserve previous tab URLs. Context picker uses existing scoped explorer reads; selected-record detail/metrics and graph use Inspector data. Conceptual stages are labelled separately from actual links. Browser verifies record selection, graph-to-detail perspective changes, original source view, catalogs, rule lifecycle and member/company boundaries, plus 16 localized Inspector layouts; shared shell verifies the new group order across 48 layouts. 133 frontend contracts, TypeScript/Vite build, 1948-key localization audit, changed-file Prettier, spec policy and diff checks passed. Context and mobile screenshots visually reviewed. No real company mutation or new backend validation claim.

FR-009/010 verification: Inspector browser passed rule-version actions, draft-editor focus, minimum expanded editor heights (340px draft/140px context), single-page pagination omission, member denial, platform-admin access without owner membership, status filter empty/active results and detail reset. All existing draft/simulation/activation, ambiguity and tenant tests remain green. Six PostgreSQL rule-service tests passed, including a new mixed-state/pagination/foreign-rule regression and HTTP query/status validation. Build, 133 frontend contracts and 1946-key four-language localization audit passed. Full backend run is recorded separately after completion.

Final combined verification: full PostgreSQL suite passed with 1790 tests and 7 existing skips (`pytest -n 4`); the focused six-test rule suite additionally verified HTTP filtering/validation. Ruff, spec policy, diff whitespace, changed-file Prettier, 133 frontend contracts, production build and 1946-key localization audit passed. The existing local API was restarted with unchanged connection settings, and its OpenAPI contract confirms rule_status is available. No live business rule was mutated during verification.

FR-011 runtime diagnosis: application-reference errors reported a registry mismatch between three new catalog classes and an old loaded service module. The existing local API was restarted with its original launcher; subsequent application-reference requests returned HTTP 200. No catalog validation was bypassed. Inline catalog/history use their existing read endpoints and preserve modal entry points.

FR-011 verification passed: Inspector browser proves direct catalog content and history table with no initial dialog and no unsupported sort/page-size controls; existing command/projection and rule paths remain green. Activity drawer browser passed cursor paging, retries, races, tenant isolation, focus and 16 localized layouts. Shared table browser passed density/persistence/sort/paging and 24 layouts. Production build, 133 contracts, 1944-key four-language audit, formatting, spec policy and diff checks passed. Inline history screenshot visually reviewed. No backend implementation changes in this increment; previous 1790-pass/7-skip baseline remains applicable.

### Register and catalog presentation verification (FR-012/013)
- Fact rules: shared table, direct New rule, modal edit/create, 50 default rows and
  25/50/100 server page sizes. Inspector fixture verifies review/simulation and
  uncertainty locks, member permissions, Escape and return focus.
- Fixed definitions and record collections use InspectorCatalog/InspectorDisclosure.
  Browser verifies filtering, empty/reset feedback, action form and projection data,
  direct exceptions/history, and no additional Inspector application-reference request on exceptions (the global
  action launcher retains its own metadata read).
- German desktop 1440px and mobile 390px screenshots checked for all four catalog
  surfaces; no document-level horizontal overflow. Rule register checked at both widths.
- Local catalog benchmark (five loads each): previous mean 894ms, optimized mean 38ms.
  This measures catalog construction, not network or total page latency. Evidence parsing
  falls from 42 parses of the same file to one; later requests still validate fresh files.
- Frontend: build, 133 contracts and 1943 localization keys in EN/DE/NL/ES pass.

### Graph autocomplete and final refinements (FR-014)
- Typed explorer HTTP regression: every supported kind, Fact predicate and ID searches,
  ten-result bound, foreign-tenant exclusion and unknown-kind 422. All seven HTTP boundary
  tests pass. Existing unfiltered explorer continues its original collection behavior.
- Inspector browser: delayed obsolete response, keyboard and click selection, failure/retry,
  type-reset/no-match, manual ID and unchanged graph links. Embedded Facts help and the
  rule catalog-count preamble are absent. Build and 133 frontend contracts pass; final
  localization inventory is 1941 keys in each of EN/DE/NL/ES.
- Backend run: 1779 passed and seven skipped; thirteen migration cases initially lacked
  Alembic configuration because the command ran from the repository root. All thirteen
  passed when rerun from packages/reality-core. Subsequent seven HTTP boundary cases pass,
  including the newly added graph lookup regression. Ruff and spec/diff checks pass.

### Automatic graph and graph-first Overview (FR-015/016)
Shared graph-start selection uses existing scoped explorer/Inspector endpoints only.
Candidate ordering follows the existing explorer (recent where timestamps are available);
there is no global most-connected-record claim or fabricated relationship. Browser proofs
cover the more-linked candidate, category switching, explicit roots, empty company,
error/retry, manual input winning a delayed automatic lookup, automatic Overview details,
linked-node detail updates and graph-before-search layout. Desktop/mobile visual checks use
1680px and 390px widths; graph nodes fit the panel by default and no document overflow occurs.
Backend unchanged for this refinement; the previously recorded backend evidence applies.
Final FR-015/016 verification: Inspector browser suite passes, including automatic selection,
retry, cancellation and graph/detail navigation; production build, 133 frontend contracts,
1943 localization keys in all four languages, Prettier and spec/diff checks pass. The 1680px
and 390px Overview screenshots were reviewed after adding the responsive stacked layout.

### Projection data dialog (FR-017)
Open view data now opens a labelled native modal backed by the existing tenant-scoped
projection endpoint. The shared table shows up to 100 returned rows; technical JSON stays
collapsed. Browser fixtures verify returned cells, Escape and trigger focus restoration,
error/retry, empty results, Close and refetch on reopening. The dialog screenshot was
reviewed. Production build, 133 frontend contracts and 1944 localization keys in each of
EN/DE/NL/ES pass. No backend behavior changed; prior backend evidence still applies.
Spec and diff checks pass. Verification uses isolated fixtures, not live business writes.

FR-017 register follow-up: Browser regression passes for catalog Items (previously routed)
and the Inventory workspace view, asserting real fixture cells in the common modal and
an unchanged catalog URL. Existing projection error/empty/retry/focus and Inspector suite
also pass. Production build, 133 contracts, all four locale audits and spec/diff checks
pass. Review confirms no remaining catalog route or activity-drawer dispatch; existing
scoped APIs are reused with no backend changes.

### Catalog orientation and destinations (FR-018/019)
Both column pairs pass desktop side-by-side and mobile stacked geometry checks. Hover
opens help and leaving dismisses it; keyboard focus and touch-like click open the ERP
examples. Desktop and mobile help screenshots were reviewed. Existing action forms and
data dialogs still pass the Inspector browser suite. Documentation links use the configured
origin, the existing catalog page and a new tab; the application link reaches Master data
while retaining tenant t1. Link targets are checked against local docs content; no claim
is made that a deployed docs service was probed. Build, 133 frontend contracts, all four
locale audits (1946 keys), spec policy and diff checks pass. No backend changes.

### Local dashboard schema repair
The shared local database remained at 0044_playground_returns_merge while the running
API expected 0045_lot_expiry. Dashboard exception derivation failed on missing
lot.expires_at. Applied the existing 0045 migration (one nullable date column, no backfill)
and verified tenant_dashboard for the affected tenant returns all expected response
sections. Spec impact: none; environment repair restores spec 109 DR-001 without changing
application behavior or business records. No new migration or schema design was added.

FR-019 sidebar extension: Production build passes. Source review verifies Documentation
below Settings, configured DOCS_URL, target=_blank, noopener/noreferrer and external icon.
Existing translation reused. Spec policy and diff checks pass; no backend changes.

### Progressive catalog explanations (FR-020)
The reference regression first failed on absent source metadata, then passed for every
command/projection contract: repository-relative paths stay inside the package, files
exist and the named functions exist in parsed Python. All seven HTTP boundary tests pass.
Browser checks cover collapsed raw definitions, the reservation example, reads/writes,
input descriptions, implementation link, projection outputs and the preserved data/action
flows. The expanded explanation screenshot was reviewed. Production build, 133 frontend
contracts, 1973 locale keys in each language, Ruff and spec/diff checks pass. The local
API was restarted to serve source references. Source links target repository main files;
no exact deployed-revision or line-number claim is made.

### Inline Python code (FR-021)
The new HTTP test first failed at the missing endpoint, then all eight boundary tests
passed. Source for commands, actions, projections and both view types contains actual
named Python functions; arbitrary paths/kinds/non-catalog functions are rejected. Added
line-count and multibyte byte-limit tests pass. Browser verifies code text, function
switching, truncation notice, error/retry, Close and Escape restoring focus, along with
the existing Inspector flows. The code dialog screenshot was reviewed. Build, 133
frontend contracts, 1982 locale keys in all four languages, Ruff and spec/diff checks
pass. Local API restarted; its log confirms successful real code reads for document
views and inventory/journal projections. Source is fetched only on demand.

### Scannable catalog cards (FR-022)
Shared card layout places the action/link row before secondary technical details. Browser
regression verifies ordering, 390px wrapping/no document overflow and all existing form,
data and code dialogs. Desktop/mobile structured-card screenshots were reviewed. Build,
133 frontend contracts, four locale audits and spec/diff checks pass. Backend unchanged;
previous API evidence applies.

FR-023 verification: source configuration browser passes all review/recovery and eight localized responsive cases; isolated CSV import browser passes. Production build, 1980-key locale audit, 133 contracts and spec check pass. Table inset geometry verified at >=16px.

FR-024 verification: production build PASS; localization audit 1988 keys per language PASS; 133 frontend contracts PASS; spec policy/diff whitespace PASS. Inspector browser suite PASS including flight recorder multi-day cursor append, retained rows after older-read failure, retry, exact source modal, empty company and delayed company-switch read; previous catalog/rule/graph regressions remain green. Desktop/mobile screenshots reviewed under /private/tmp/reality-138-browser/flight-recorder-*.png. Uses existing timeline service; no backend or schema changes. Review confirms explicit references only, no inferred causal links or historical-state reconstruction.

FR-025 verification: production build PASS, all four language audits PASS (1988 keys), 133 frontend contracts PASS, spec policy and diff whitespace PASS. Reviewed Shell/page labels and adjusted existing source-browser selectors. URLs and source registration behavior unchanged; no additional behavior tests required for wording-only change.

FR-026 verified: three graph-model tests, 136 frontend contracts, production build, 1991-key localization audit and full Inspector browser suite PASS. Reviewed desktop/mobile lane screenshots; older prepend retains horizontal time anchor, repeated source identity is singular, node selection opens details, previous paging/retry/company isolation remains green. Final heading is Understand context.

FR-027 verification: 10 focused service/HTTP tests PASS including 28-item pagination, cross-tenant search exclusion, all-family metadata and invalid kind/page/size. Production build, 1998-key four-language audit, 136 frontend contracts, Ruff and spec policy PASS. Full Inspector browser suite PASS including all-record default, source-type selection/reload, source detail dialog, switching to the original Facts table and existing graph/catalog/rule flows. Reviewed register screenshot. Local API restarted on port 8007 and live inspector-records reads return 200. No schema or business mutations.
