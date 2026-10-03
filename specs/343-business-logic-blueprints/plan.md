# Implementation Plan: Explainable Business Logic and Test Blueprints

**Branch**: `codex/add-advisor-new-chat` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)
**Language**: English for repository artifacts.

## Summary

Provide one read-only application service that derives explanations from the loaded implementation and shipped test source on each request. Reuse catalog source inspection and runtime registrations; parse bounded source into a source-cited decision graph, render business steps and diagrams from that graph, and discover actual tests and their assertions. No saved blueprint prose, generated explanation catalog, alternative business engine or business schema is introduced.

The initial release inventories every public entry and fully exercises the credit exposure → credit hold → delivery readiness → owner-confirmed hold release journey. Unsupported interpretation is explicitly partial, not silently approximated. The release gate requires all decision branches within the documented reference boundary to be represented with source evidence and actual test links or explicit gaps.

## Technical Context

**Language/Version**: Python 3.12+, TypeScript/React, Vue in existing VitePress docs.
**Primary Dependencies**: Python ast/inspect/hashlib, existing Pydantic v2/FastAPI, shared tool/MCP registries; existing localization and frontend rendering. No new model provider is required.
**Storage**: No new business tables or migrations. Source/test evidence is immutable release content. Optional test results are existing CI evidence, never inferred from test presence.
**Testing**: pytest unit/service/story/adapter, focused browser scripts, frontend/docs builds, full repository gates.
**Project Type**: Shared application core with API, MCP, Chat and separate static presentation deployments.
**Constraints**: Decimal strings; UTC; opaque identifiers; strict tenant scope; no test execution or business mutation during explanation.
**Scale/Scope**: Complete public inventory; bounded analysis of one entry per detail request; deep initial reference journey. Limits: 64 resolved functions, 2 MiB source, helper depth 8, 200 discovered scenarios, 5-second analysis budget. Exceeding a limit returns partial with omitted evidence listed. A reference request exceeding a limit fails the completeness release gate rather than hiding branches.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Generic explanation is not business authority; concrete case reads retain existing shortest provenance links | PASS |
| Reality owns operational state | Read existing exposure/hold/readiness services; add no document status or alternate calculation | PASS |
| Proven schema only | No new business schema; evidence models are response contracts | PASS |
| Tenant + shared service boundaries | One service for all channels; generic public reads cannot accept company IDs; private reads retain existing tenant authorization | PASS |
| Spec/test traceability | Requirement groups mapped below; tests precede implementation tasks | PASS |
| Explainable web behavior | Source-cited decisions, diagrams and actual test assertions in existing catalog detail surface | PASS |
| Received values not recomputed | Parse expressions without executing financial calculations; concrete values come from existing services | PASS |
| Smallest coherent design | Existing runtime source inspector, Python AST and deterministic rendering; no rule engine, new provider or queue | PASS |

Pre-design and post-design checks pass. User continuation accepted specification scope. No constitutional exception is proposed.

## Repository Structure and Layer Changes

Existing integration points:

- `packages/reality-core/src/reality/catalogs.py`: existing `catalog_code`, runtime catalog, service resolution; extract validated root resolution for shared use without changing existing catalog behavior.
- `packages/reality-core/src/reality/mcp/catalog.py`: tool handlers, schemas and canonical application names.
- `packages/reality-core/src/reality/tools/application.py`: canonical read dispatch and action/service routing.
- `packages/reality-core/src/reality/web/api.py`: existing catalog-code and application-reference routes; private detail/comparison routes delegate only.
- `packages/reality-core/src/reality/web/read_models.py`: current register readers used by view roots.
- `apps/web/src/unified/CatalogEntryDetails.tsx`, `CatalogCodeDialog.tsx`, `toolCatalogEntries.ts`, `apps/web/src/api.ts`: live blueprint detail, source navigation and test scenarios.
- `apps/docs/.vitepress/theme/components/ToolUsage.vue`: fetch live details, show target release and unavailable/retry states.
- `apps/docs/scripts/generate-catalog-reference.py`: continue generating vocabulary metadata only; no blueprint prose/diagram generation.
- `apps/api/Dockerfile`, `apps/mcp/Dockerfile`, root `Dockerfile`: carry approved test source and helpers belonging to the exact release; build a file-digest manifest only, never explanations.

New bounded modules:

- `domain/business_blueprints.py`: immutable response graph, evidence identities and conservative comparison types.
- `services/business_blueprint_source.py`: runtime root/call resolution and exact-source checks.
- `services/business_blueprint_analysis.py`: AST decision/test extraction without execution.
- `services/business_blueprints.py`: discovery, detail, safe source retrieval and private comparison orchestration.
- `web/business_blueprint_api.py`: public generic read routes; no tenant/session dependencies or company inputs.

Names above are relative to `packages/reality-core/src/reality/`. Business labels come from existing catalogs/data model and ordinary localization dictionaries; they are vocabulary, not authored logic.

## Design

### Reality flow

Generic request → validated registered operation → loaded callable source → helper/decision graph → related test source/assertions → response. This has no SourceRecord or Evidence write stage because it explains deployment code, not a business transaction.

Concrete case → current authorized shared read → available Reality and evidence links → comparison with extracted test conditions. Never execute the operation to explain it. Existing credit-hold event facts can explain recorded decisions; otherwise explicitly label a current-state evaluation.

### Service and adapter flow

Canonical tools `business_logic_discover`, `business_logic_explain`, `business_logic_source` and `business_logic_compare` call the shared service. Chat and remote MCP use identical bindings. Generic HTTP uses the same service without a database session. Authenticated company routes and the comparison tool use existing session/tenant authorization. Public source access is an approved narrower projection of the same evidence.

Runtime callable selection is server-owned. Commands, projections, actions and views reuse catalog mappings; tools resolve canonical dispatch and preview/execution handlers, not just wrapper lambdas. Source identity comes from the imported function's code object, source path and digest plus release identity. Request-time checks reject disk content inconsistent with loaded function code. Development working-copy changes require process reload; a changed file is not falsely presented as running logic.

Use a small explicit resolver table only where runtime dispatch cannot be statically resolved. It contains callable identities and edges, never business prose or outcomes, and is validated against executable bindings. Stable rule markers can be inert source comments adjacent to decisive expressions; values/operators still come solely from live AST. Moving or altering a marked decision keeps its identity but changes its digest. Unmarked rules use qualified function plus structural identity and disclose identity stability limits.

Parse supported branches, guards, assignments, returns, comprehensions, aggregations, literal error codes, service calls and SQLAlchemy predicates into a typed graph. Preserve > versus >=, positive-limit guards, currency filters, source-stated value usage, side-effect calls and helper relationships. Unsupported calls/predicates are opaque nodes with citations and limitations. Never use eval, import caller-specified modules, invoke tests or evaluate SQL to discover behavior.

Render controlled business templates over this graph and existing business labels at request time. Diagram edges and prose use the same nodes. Reject or mark partial any business label that would imply unsupported semantics. No LLM is needed for generic explanations; Chat can phrase the grounded tool result through its existing provider, with evidence-bound instructions. Public docs therefore need no company AI credentials or new paid provider. Analysis freshness and semantic completeness are separate fields.

Tests are parsed from approved actual release source, including helper fixtures and parameter decorators. Call/AST relationships discover candidate tests; assertion and data-flow relationships distinguish demonstrated rule evidence from mere candidate association. Only supported literal/Decimal/fixture facts become comparable conditions. Unresolved fixture setup stays unknown. There is no claim of measured branch coverage without matching execution evidence.

### Reference journey boundary

Actual implementation anchors: `services/credit_exposure.py`, `services/credit_hold_actions.py`, `services/fulfillment_readiness.py`, applicable order-intake/correction callers, and canonical owner/confirmation routing. Source tests: `tests/test_credit_exposure.py`, `tests/test_credit_hold.py`, `tests/test_credit_hold_adapters.py` and readiness tests where related.

The existing exposure expression is open invoices + not-yet-invoiced open orders − available credits. The positive-limit and strict-greater-than check means zero is no configured limit and equality does not exceed it. Payables are named rather than netted; currency exclusions and unpriced lines matter. An over-limit new sales order is recorded and held, not rejected at intake. A credit hold and owner release are separate from general delivery readiness; releasing credit holds does not remove unrelated blockers. These observations guide regression expectations only: their displayed expressions are extracted from live source, never hard-coded as blueprint prose.

### Data and migration impact

No migration. Ship exact approved synthetic tests and necessary fixture source as non-executable release evidence, with relative paths and file digests. Use installed runtime modules as business source authority. Manifest compilation at build time is allowed solely to establish provenance of raw files, not pre-generate explanations. Test-run evidence is optional and defaults to unknown; an unavailable CI link cannot be displayed as a passing result.

### Failure, security, and tenant behavior

Accept only catalog IDs and server-issued evidence IDs, never paths, expressions or import strings. Bound dependency traversal to approved business modules; block security/authentication secrets, provider credentials and arbitrary infrastructure source. Public test/source roots must be explicitly reviewed; no whole repository export. Symlinks/path traversal are rejected. No mutable tenant payloads enter generic explanation state.

Generic public endpoints have rate limits, response/source size caps, fixed configured docs-origin CORS and no cookies or tenant access. Access restrictions and refusal labels may be described generically without exporting secret/security implementation. Wrong tenant reads return not found. Rendering treats source/docstrings as untrusted text, not instructions or HTML; diagram identifiers and labels are escaped.

A request captures one source/evidence revision; changed files during analysis invalidate the response. Mixed API/MCP releases expose differing revisions instead of claiming parity. Unknown providers, unavailable source, ambiguous fixture resolution or timeout return explicit limitations and safe partial output.

## Test Strategy and Traceability

All paths below are planned; creation/execution belongs to tasks and implementation.

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-004, DR-004 | Unit/service | `tests/test_business_blueprint_inventory.py` | Inventory and shared-rule resolution absent |
| FR-002, FR-003, FR-005, FR-006, FR-017–FR-019 | Unit | `tests/test_business_blueprint_analysis.py` | No guarded-expression graph, source verification or dynamic render |
| FR-007–FR-009 | Unit/service | `tests/test_business_blueprint_tests.py` | No fixture/assertion extraction or version-bound run statuses |
| FR-010, FR-016 | Browser/build | `apps/web/scripts/business-blueprints-browser.mjs`; docs component checks | No live diagram/test display, fallback or target-version states |
| FR-011, FR-014, DR-003 | Adapter | `tests/test_business_blueprint_adapters.py` | Canonical read tools/public-safe routes absent |
| FR-012, FR-013, DR-001, DR-002 | Service/story | `tests/test_business_blueprint_cases.py` | No conservative test comparison or explicit historical/current split |
| FR-015 | Story | `tests/scenarios/test_credit_blueprint_journey.py` | Full credit journey graph and test references absent |
| FR-005, FR-018, FR-019 | Packaging | `tests/test_business_blueprint_release.py` | Production test evidence absent; loaded/disk mismatch not checked |

Test fixtures must alter source decision operators, fixture values and assertions without generating explanations, then reload the controlled fixture module and verify the next response. Also test changed disk without reload, partial helper resolution, arbitrary-path requests, public tenant-field rejection, malicious labels and source provenance mismatches. Existing credit behavior tests remain untouched unless inert identity annotations need verification. Full backend suite, lint, spec check, web build/i18n/browser suite, docs generation/catalog check/docs build and release evidence smoke checks are required before completion.

## Rollout and Rollback

Ship source/test evidence with backend release first. Deploy shared read tools and routes, then Web/docs clients with explicit unavailable-target handling. Public docs live target is deployment configuration, not a caller-supplied URL; it points to the API generic endpoint and identifies the responding release. Preserve existing catalog/code views. Rollback restores the matching complete repository release; no data rollback or background jobs are needed.

## Review Risks

- Translating opaque helpers or SQL into unjustified semantics: partial is mandatory, and the reference completeness gate must be demonstrated before release.
- Source disclosure or costly public traversal: reviewed allowlist, bounded server-owned IDs and rate limits.
- Tests absent from images, fixture dependencies or inconsistent loaded/disk versions: explicit evidence packaging and artifact smoke proofs.
- A discovered test mistaken for passing execution or complete coverage: separate discovery, assertion links and run evidence.
- Multi-tenant context entering public responses: generic service API has no tenant inputs; tenant cases are separate.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## ERP readability correction

Add an immutable business-presentation response model and a shared deterministic semantic renderer in services/business_blueprint_presentation.py. It parses the already verified current source expressions, maps vocabulary (not per-tool rules), and emits only supported business statements. No model-provider dependency, saved explanations, schema or alternate calculation is introduced. Each step retains its RuleNode identity and evidence link; omitted technical nodes are traversed to contract the original same-function graph while preserving branch labels. Technical analysis remains available. Unknown names/expressions are counted and disclosed instead of guessed. Parse actual test assertion expressions and known facts for Given/When/Then; do not execute tests. Both adapters render the server response, and MCP/Chat receive the same contract. English/German are supported; other languages explicitly fall back to English.

Constitution recheck: all existing rows PASS. Response-only models, no business writes, no financial recomputation, source links and tenant scope unchanged. Test-first: semantic threshold/operator mutation, whitelist-value mutation, currency guards, effects, unresolved semantics, graph contraction, test assertion provenance and safe escaped localized adapter rendering. Run focused Python blueprint tests, docs/frontend checks/builds and real live-browser reference reads; record broader suite limitations honestly.

### Superseding renderer design after live LLM clarification

Replace the proposed vocabulary-only renderer with a generic request-time model interpreter using the existing deployment Anthropic provider configuration and httpx. This explicitly supersedes the original no-provider constraint for the presentation layer; source analysis remains deterministic. One bounded structured-output request includes only verified source, RuleNodes/edges and approved tests. Pydantic validates response sizes, exact known rule/test identities and duplicate IDs; server supplies source links and contracts the original graph (the model never draws independent edges). Citation validation does not certify semantic correctness. No response cache or persisted prose. Missing configuration, HTTP/schema failures, source drift or concurrency limits produce an explicit unavailable business view. Source/compare reads suppress model interpretation to avoid unrelated paid calls. Revalidate source/test bytes after the model response before returning it. No tenant credentials or company data are passed to the deployment provider. Tests use a fake provider to exercise arbitrary previously unknown operations, prompt changes after source changes, invalid citations, provider errors, output bounds, graph fidelity and no writes. Validate actual live credit/item generation where configured.

Constitution recheck PASS: shared read service, request-only response, no schema or alternate business engine. LLM-generated text is inference with traceable evidence, never business authority. Public admission and shared concurrency limits remain bounded. No recurring work.

### Loading and responsive flow correction

User-requested adapter-only improvement. Shared flowCards helper numbers supplied steps and resolves only supplied edges. Replace primary SVG with wrapping HTML cards and numbered branch links in Vue/React; retain technical SVG. Add request-lifetime elapsed timer and accessible spinner with reduced-motion support. No business calculations, provider change or schema. Constitution Check: all rows PASS. Test delayed browser response, full long text and actual branch fidelity, desktop/mobile bounds, then both builds and adapter checks.

Latency correction: optional brief flag in shared explain/presentation and HTTP adapters, default false for existing MCP/full reads. Brief request omits synthetic test bodies/helpers and graph edges from provider envelope (server owns graph), caps six output steps with smaller token allowance. All current source/rule evidence is retained; no unsafe dependency truncation. UI offers full read on demand. Constitution PASS. Add regression for prompt boundary and source/citation retention; measure actual provider response time, never certify target without evidence.

Chat discovery recovery (FR-011 bug fix): shared discovery collects query matches before applying kind, returns at most 10 alternate kind identities only for an empty filtered result, with bounded count/truncation and honest recovery hint. Existing filtered result semantics remain unchanged. Chat system instruction defines entry kinds and prohibits existence/test claims from failed search. Regression first for real credit and an unseen arbitrary catalog entry; actual Anthropic Chat/MCP tool-loop test. Constitution all rows PASS: generic read-only vocabulary, no company reads, schema, saved answers or business calculations.

Actual live Chat additionally reproduced HTTP 400: 311155 input tokens exceeded the provider 200000 limit after a full command blueprint. Add a response-only Chat projection for business_logic_explain in both provider loops: retain current business interpretation, source identities, raw test facts/assertions/run state and bounded decisive technical rules; omit expanded graph paths and raw source/helper bodies from the initial chat envelope. Explicit total/shown counts and omissions; on-demand source tool remains canonical. No model answer cache or alternate business semantics. Budget 120000 UTF-8 bytes and deterministic omission until below bound; error fallback preserves source availability and does not claim no tests. Regression first verifies source IDs, tests, totals, no fabricated passing run and no mutation of the original MCP response.

Chat response traceability: append a deterministic localized evidence footer for successfully read blueprints in either provider loop. It states discovered scenario count (not passing runs) and offers bounded source links using exact returned source IDs. This supplements model prose without asserting that every sentence is verified. Add unit proof; unrelated answers remain unchanged.

### UX hierarchy and source focus correction

Use shared response-only sourceRanges/sourceExcerpt helpers against already loaded source and RuleNode identities. Backend already emits end_line; add it as optional to shared TS node. For control-flow nodes, highlight the short header/start rather than whole nested blocks; for other statements use their verified span. Source UI starts near first span with context and offers full-function toggle, scrolling within code pane only. React/Vue source widgets render escaped text with line gutters, semantic highlight and unknown-span notice. Three local tabs separate rules/tests/technical; selected test uses the existing canonical comparison flow. No model request, business calculation, source modification, database schema, cache or transport change. User-authorized UX reviewer provided recommendations; all Constitution rows PASS. Regression tests first for exact offsets, unrelated helpers, ranges and untouched code; adapter/browser keyboard/selection/layout proofs and both builds follow.

### Sequential reading refinement

User review prefers Chat-like steps over a separate flow diagram. Extend the generic live interpretation instruction to put supported conditions/actions/alternatives on separate labeled lines in the existing step text. Preserve response schema, source citations and output bounds; do not parse arbitrary prose into inferred branches. Both adapters render multiline text verbatim, label cards as steps and remove the duplicate business flow view. Technical graph remains secondary. Tests cover multiline retention, absence of the duplicate flow view and existing source navigation. Constitution Check PASS: presentation-only, no persisted authority or alternative business rules. Analysis: FR-028 maps T063; no critical conflicts or unresolved clarification.

### ERP explorer entry refinement

User approved localized business-object names, familiar navigation order and useful read-only entry shortcuts while retaining the existing two-column explorer. Change presentation only: localized resource labels from the executable catalog, stable known-object ordering with all other objects retained, and shortcut buttons resolved against returned catalog entry IDs before display. Do not execute tools or auto-load live evidence from navigation. Keep technical/data-model vocabulary unchanged. Tests first: actual Vue SSR German card ordering/labels, English fallback and shortcut presence; browser navigation and mobile layout; complete Docs contract/build checks. Constitution Check PASS. FR-029 maps T064; no unresolved clarification or critical conflicts.

### Explanation entry wording

User approved a benefit-oriented explanation entry rather than technical live-logic wording. Update Docs labels and visual action hierarchy only: initial question/primary explanation action, loaded heading/provenance and secondary refresh action. No prefetch, provider, source or response changes. Tests first for initial question/action and loaded provenance/refresh; existing browser freshness/loading/retry journey follows the new accessible names. Constitution Check PASS; FR-030 maps T066; no unresolved clarification or critical conflicts.

### Business-first function detail

User review supersedes FR-030's prominent separate initial card: lead with catalog-localized business title and one description; position a borderless inline explain action below it, retaining loaded explanation controls. Move existing technical content after this introduction without changing execution. Optional descriptions.de catalog entries provide manually maintained purpose translations, distinct from dynamically inferred rules. Preserve technical English labels/IDs in technical browsing. Tests cover reordered SSR details, localized purpose and unchanged identifiers; source explanation remains on demand. Constitution Check PASS; FR-031 maps T067; no critical conflict or unresolved clarification.

### Direct code entry and exception coverage

User requests clearer code access and checks read/exception coverage. Add a bounded public source-only request flag that delegates to the existing explain service with interpretation disabled, with a direct source tab in Docs. Keep the separate explicit interpretation action. Views/projections remain existing registered roots. Extend inventory to registered exception definitions and their actual shared exception evaluator; disclose shared scope and retain partial status. Never invoke the evaluator or query company records. Tests first: interpreter is forbidden during source-only reads, exception inventory/source scope, Vue code control and browser raw-source display. Constitution Check PASS; FR-032 maps T068; no unresolved clarification or critical conflict.

### Source inspection audit

Review: FR-035 restores accurate source navigation under FR-032; no unresolved clarification or critical finding. Constitution check passes: read-only inspection of existing callables and executable builder registry, no schema or business-rule changes. Verify catalog-wide view/projection source coverage and bounds, MCP rejection handler, original source line rendering and failure/retry behavior before completion. Preserve the user-approved primary function plus collapsed helpers and removal of redundant source controls.

### Shared projection-tool routing

FR-036 review: preserve one inspection service for every surface. Inspect approved loaded source AST for calls to the existing shared `_projection_read` callable and fixed name binding; append roots from the actual projection registry. Retain adapter roots and partial/shared-scope disclosure. No call execution, arbitrary attribute lookup, inferred name matching, data reads, schema changes or authorization changes. Constitution check passes; no unresolved clarification or critical finding. Red-first regression compares public tool, MCP and direct projection evidence; test future renamed adapters and reject dynamic-name inference.
