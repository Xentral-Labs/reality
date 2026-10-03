# Tasks: Explainable Business Logic and Test Blueprints

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts](contracts/business-blueprints.md), [quickstart.md](quickstart.md).
**Gate**: User accepted scope for planning; all Constitution rows PASS. Analysis must have no CRITICAL findings before implementation.
**Language**: English for every repository artifact. No schema change or background job is planned.

## Format and execution rules

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

All tasks start unchecked. Tests precede the implementation they prove; observe meaningful failure before implementation where practical and record it in `verification.md`. A `[P]` marker denotes independent files within an eligible phase, not permission to skip dependencies. Story counts exclude foundation/cross-cutting tasks. Paths are repository-relative except short feature-file links explicitly identified below.

## Phase 1: Specification and Design Gates

- [x] T001 Record accepted scope, Constitution PASS and custom-checklist review state in `specs/343-business-logic-blueprints/checklists/live-evidence.md`; preserve reviewer-owned markers and identify pending decisions instead of marking them approved.
- [x] T002 [FR-015] Enumerate exact reference roots, relevant helper symbols and outcome-affecting guards with current source citations in `specs/343-business-logic-blueprints/contracts/reference-boundary.md`; cover exposure/currency/source amounts, hold creation/replay, readiness and owner-confirmed release; exclude only framework internals, never an unresolved outcome decision.
- [x] T003 Run read-only Spec Kit analysis of `specs/343-business-logic-blueprints/spec.md`, `plan.md` and `tasks.md`; address CRITICAL findings before code and record the reviewed gate outcome in `specs/343-business-logic-blueprints/verification.md` during implementation.

## Phase 2: Foundation and failing source proof

Foundation unlocks every story. No external source execution, ORM mutation or stored explanation is introduced.

- [x] T004 [P] [FR-005] [FR-006] [FR-014] [FR-017] [FR-018] [FR-019] Add failing provenance/security tests in `packages/reality-core/tests/test_business_blueprint_release.py`: loaded-versus-disk mismatch, release reload, changed files during analysis, package missing source/tests, symlink/path escapes, matching raw-file digests and no explanation-generation step.
- [x] T005 [P] [FR-004] [DR-004] Add failing graph/identity contract tests in `packages/reality-core/tests/test_business_blueprint_analysis.py`: duplicate durable markers, revision-local unmarked nodes, Decimal/time representation and unknown/partial states.
- [x] T006 [FR-004] [FR-005] [FR-006] [FR-009] [DR-004] Define immutable graph, source, scenario, run-evidence and comparison response types in `packages/reality-core/src/reality/domain/business_blueprints.py`; keep freshness, semantic completeness and execution outcome separate, with no business database model.
- [x] T007 [FR-005] [FR-006] [FR-014] [FR-017] [FR-018] [FR-019] Implement allowlisted runtime callable inspection and request-consistent digest checks in `packages/reality-core/src/reality/services/business_blueprint_source.py`; normalize trusted compiled source against loaded qualified code without execution, fail unsupported provenance honestly and accept only registry/evidence IDs.
- [x] T008 [FR-005] [FR-007] [FR-018] [FR-019] Package reviewed actual synthetic tests/helpers as raw release evidence using `scripts/package_business_blueprint_evidence.py`, `apps/api/Dockerfile`, `apps/mcp/Dockerfile` and `Dockerfile`; generate digests only, never business descriptions, and leave incomplete fixture dependencies visible.
- [x] T009 [FR-005] [FR-018] Run T004/T005 proofs and API/MCP image evidence smoke checks, recording command outcomes and artifact revisions in `specs/343-business-logic-blueprints/verification.md`; do not call provenance complete if only checkout tests pass.

## Phase 3: US1 — Inspect a business operation (P1)

**Goal**: Dynamically inspect the real business steps, diagram and source of a catalog entry.
**Independent acceptance**: US1.1–US1.5, with credit reference rules showing exact decisions and source versions; all public entries remain discoverable even without resolved logic.

### Tests first

- [x] T010 [P] [US1] [FR-001] [FR-004] [DR-004] Add failing full-inventory tests in `packages/reality-core/tests/test_business_blueprint_inventory.py` for commands/tools/actions/views/projections, business-topic search, canonical shared-rule roots and explicit missing statuses.
- [x] T011 [US1] [FR-002] [FR-003] [FR-006] [FR-017] [FR-019] Add failing live analysis tests in `packages/reality-core/tests/test_business_blueprint_analysis.py` for guard order, > versus >=, zero-limit handling, expressions, SQL filters, refusals, supported effects, helper calls and opaque nodes; mutate source operators and reload to prove next-read freshness.
- [x] T012 [P] [US1] [FR-005] [FR-014] [FR-018] [DR-003] Add failing generic-route and read-only tests in `packages/reality-core/tests/test_business_blueprint_adapters.py` for unknown IDs, tenant-field rejection, unsafe source suppression, escaped labels, configured origins, admission limits and unchanged catalog-code behavior.
- [x] T013 [P] [US1] [FR-003] [FR-005] [FR-010] [FR-016] Add initial operation-view browser cases in `apps/web/scripts/business-blueprints-browser.mjs` for business steps/graph equivalence, source/version navigation, unsupported/loading/retry states, keyboard/text alternative and English fallback.

### Domain → service → adapters

- [x] T014 [US1] [FR-001] [FR-004] [DR-004] Extract reusable registered-root resolution from `packages/reality-core/src/reality/catalogs.py` and view readers in `packages/reality-core/src/reality/web/read_models.py`; inspect actual canonical handlers from `packages/reality-core/src/reality/mcp/catalog.py` and `packages/reality-core/src/reality/tools/application.py`, retaining unrelated inventory entries with missing status.
- [x] T015 [US1] [FR-004] [FR-015] [DR-004] Add inert durable identity markers to outcome-affecting reference decisions in `packages/reality-core/src/reality/services/credit_exposure.py`, `credit_hold_actions.py` and `fulfillment_readiness.py`, plus exact caller symbols identified by T002; marker text carries identity only and existing behavior/tests remain unchanged.
- [x] T016 [US1] [FR-002] [FR-003] [FR-006] [FR-017] [FR-019] Implement bounded source-cited AST/data-flow graph extraction and request-time business rendering in `packages/reality-core/src/reality/services/business_blueprint_analysis.py`; text and diagrams use the same nodes, preserve operators/units and report unsupported semantics and traversal omissions explicitly.
- [x] T017 [US1] [FR-001] [FR-002] [FR-003] [FR-005] [FR-006] [FR-014] [FR-017] [FR-018] [FR-019] Implement discover/detail/source orchestration in `packages/reality-core/src/reality/services/business_blueprints.py`; resolve one exact evidence set per request, expose no mutable tenant data and never read a saved explanation as authority.
- [x] T018 [US1] [FR-005] [FR-010] [FR-014] [DR-003] Add generic safe read routes, bounded admission and fixed configured CORS in `packages/reality-core/src/reality/web/business_blueprint_api.py` and register them in `packages/reality-core/src/reality/web/app.py`; add tenant-private read delegation in `packages/reality-core/src/reality/web/api.py`, preserving existing authorization.
- [x] T019 [US1] [FR-003] [FR-005] [FR-010] [FR-016] Add typed live reads and business/source presentation in `apps/web/src/api.ts`, `apps/web/src/unified/CatalogEntryDetails.tsx` and `CatalogCodeDialog.tsx`; register the browser script in `apps/web/scripts/browser-suite.json` and use existing localization files referenced by `apps/web/src/localization.tsx`.
- [x] T020 [US1] [FR-001] [FR-002] [FR-003] [FR-005] [FR-006] [FR-017] [FR-018] [FR-019] Run US1 independent proofs and record inventory denominator, branch extraction limits and next-request source-change results in `specs/343-business-logic-blueprints/verification.md`.

## Phase 4: US2 — Inspect tested business cases (P1)

**Goal**: Show actual tests as readable business cases without inventing fixtures, assertions or execution results.
**Independent acceptance**: US2.1–US2.4 using real credit tests; test discovery and missing branch evidence work without Chat or case comparison.

### Tests first

- [x] T021 [P] [US2] [FR-007] [FR-008] [FR-016] [FR-017] [FR-019] Add failing scenario-extraction tests in `packages/reality-core/tests/test_business_blueprint_tests.py` for real fixture setup, parameter decorators, helper facts, assertion-linked versus candidate relationships, mutated assertion freshness, unresolved setup and synthetic-only content.
- [x] T022 [US2] [FR-008] [FR-009] Add failing run/coverage evidence tests in `packages/reality-core/tests/test_business_blueprint_tests.py` for unmapped branches and passing/failed/skipped/missing/older-version/unavailable results; a discovered test or inaccessible CI artifact must not claim success or branch execution.
- [x] T023 [P] [US2] [FR-007] [FR-008] [FR-009] [FR-010] [FR-016] Extend test-case browser proofs in `apps/web/scripts/business-blueprints-browser.mjs` with setup/action/assertion detail, parameter cases, code links, explicit gaps and separate execution status.

### Domain → service → presentation

- [x] T024 [US2] [FR-007] [FR-008] [FR-017] [FR-019] Implement non-executing test/helper/fixture parsing and conservative assertion-to-rule evidence in `packages/reality-core/src/reality/services/business_blueprint_analysis.py`; use actual reviewed release files, preserve distinct cases and leave unresolved assumptions unknown.
- [x] T025 [US2] [FR-008] [FR-009] [FR-018] Add optional trusted CI artifact reads and per-version outcomes in `packages/reality-core/src/reality/services/business_blueprints.py`; default to unknown, do not accept user-provided success claims and expose missing branch evidence independent of run results.
- [x] T026 [US2] [FR-007] [FR-008] [FR-009] [FR-010] [FR-016] Add readable tested-case and execution-evidence sections in `apps/web/src/unified/CatalogEntryDetails.tsx` and source navigation in `CatalogCodeDialog.tsx`; render actual asserted effects, uncertainties and English fallback without labeling candidate tests as proof.
- [x] T027 [US2] [FR-007] [FR-008] [FR-009] [FR-015] Run US2 independent proofs against `packages/reality-core/tests/test_credit_exposure.py`, `test_credit_hold.py` and `test_credit_hold_adapters.py`, recording the case/assertion mapping and explicit gaps in `specs/343-business-logic-blueprints/verification.md`.

## Phase 5: US3 — Ask through Chat or MCP and live docs (P2)

**Goal**: The same versioned rules/scenarios are usable through Chat, MCP and the live section of public Tool Usage documentation.
**Independent acceptance**: US3.1–US3.4; no tenant case comparison is needed to ask about generic logic/tests.

### Tests first

- [x] T028 [US3] [FR-010] [FR-011] [FR-014] [FR-016] [DR-003] Add failing canonical-tool/Chat/MCP parity tests in `packages/reality-core/tests/test_business_blueprint_adapters.py`, including citations, no invented missing evidence, declared nested schemas, read access, no mutations and mixed-release labeling.
- [x] T029 [P] [US3] [FR-010] [FR-016] [FR-017] [FR-018] [FR-019] Add live-docs browser/component checks in `apps/docs/scripts/business-blueprints.test.mjs` and `apps/docs/scripts/business-blueprints-browser.mjs` for configured target, current revision, next-request changes without docs builds, graph/test/source display, text alternatives, unavailable/retry and escaped text.

### Tools → adapters → docs

- [x] T030 [US3] [FR-011] [FR-014] [DR-003] Register `business_logic_discover`, `business_logic_explain` and `business_logic_source` canonical reads in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`; adapters delegate to the same service and declare explicit nested input fields.
- [x] T031 [US3] [FR-011] [FR-016] Update grounded explanation routing/instructions in `packages/reality-core/src/reality/agent/mcp_chat.py`; preserve exact rule references, unsupported limitations, historical/current distinction and existing provider/confirmation behavior.
- [x] T032 [US3] [FR-010] [FR-016] [FR-017] [FR-018] [FR-019] Add live blueprint/test/source retrieval and matching diagram/text rendering in `apps/docs/.vitepress/theme/components/ToolUsage.vue`, configured via `apps/docs/.vitepress/config.mts`; display the responding target/revision and explicit unavailable state, with no generated final explanations.
- [x] T033 [US3] [FR-001] [FR-010] [FR-011] [FR-016] Add new tool resource membership and German ERP labels in `packages/reality-core/config/resource_catalog.yaml`; run `make docs-generate` and commit generated vocabulary pages under `apps/docs/content/tool-usage/`, `apps/docs/content/de/tool-usage/` and `apps/docs/.vitepress/data/tool-usage.json` without embedding live blueprint prose.
- [x] T034 [US3] [FR-010] [FR-011] [FR-017] [FR-018] [FR-019] Run the same reference questions through Web/docs/Chat/MCP and record rule/scenario/release parity plus inaccessible-live-target outcomes in `specs/343-business-logic-blueprints/verification.md`.

## Phase 6: US4 — Compare my case and explain a decision (P2)

**Goal**: Compare relevant test conditions honestly and explain only available current or historical values through existing tenant-scoped services.
**Independent acceptance**: US4.1–US4.4; matching/different/unknown conditions, tenant isolation and no mutations are proven using synthetic records.

### Tests first

- [x] T035 [P] [US4] [FR-012] [FR-013] [FR-014] [DR-001] [DR-002] [DR-003] Add failing service/story cases in `packages/reality-core/tests/test_business_blueprint_cases.py`: equal/different/unknown prerequisites, currency/unit/date differences, source-stated amounts, held-record provenance, current versus recorded context, changed payment state, unavailable historical version and another tenant's references.
- [x] T036 [US4] [FR-011] [FR-012] [FR-014] [DR-003] Extend `packages/reality-core/tests/test_business_blueprint_adapters.py` with structured comparison schemas, supplied fact versus authorized record exclusivity, private-only record reads, read-only transport and unchanged mutation confirmation.
- [x] T037 [P] [US4] [FR-012] [FR-013] [FR-016] Extend `apps/web/scripts/business-blueprints-browser.mjs` with test-case comparison, relevant missing inputs, current/historical labels, source links and access failure states.

### Domain → services → tools → adapters

- [x] T038 [US4] [FR-012] [DR-001] [DR-002] [DR-004] Implement conservative relevant-condition comparison in `packages/reality-core/src/reality/domain/business_blueprints.py` and `services/business_blueprints.py`; preserve Decimal/unit/time context, never recalculate source authority and never turn similarity into outcome proof.
- [x] T039 [US4] [FR-013] [FR-014] [DR-001] [DR-002] [DR-003] Resolve party/order/commitment case inputs through existing credit exposure/readiness and hold-event reads inside `packages/reality-core/src/reality/services/business_blueprints.py`; retain tenant scope and shortest evidence links, disclose unknown historical rules and add no event or derived-state storage.
- [x] T040 [US4] [FR-011] [FR-012] [FR-013] [FR-014] [DR-003] Register `business_logic_compare` in `packages/reality-core/src/reality/tools/application.py` and `mcp/catalog.py`, add private read-query delegation in `web/api.py`, update `packages/reality-core/config/resource_catalog.yaml` labels and regenerate vocabulary via `make docs-generate`.
- [x] T041 [US4] [FR-012] [FR-013] [FR-016] Add typed comparison reads and case presentation in `apps/web/src/api.ts` and `apps/web/src/unified/CatalogEntryDetails.tsx`; use existing locale formatting and preserve historical/current labels and unknown fields.
- [x] T042 [US4] [FR-012] [FR-013] [FR-014] [DR-001] [DR-002] [DR-003] Run US4 independent matching/differing/unknown/unauthorized stories and record no-write, confirmation and provenance evidence in `specs/343-business-logic-blueprints/verification.md`.

## Phase 7: Reference acceptance and cross-cutting review

- [x] T043 [FR-002] [FR-003] [FR-007] [FR-008] [FR-015] [DR-001] [DR-002] Add the end-to-end failing completeness proof in `packages/reality-core/tests/scenarios/test_credit_blueprint_journey.py` against the T002 boundary before any completeness fixes: exact outcome guards, exposure/currency rules, order recorded-and-held, replay, readiness, owner release and remaining blockers; assert every listed branch has source evidence and actual test links or an explicit gap.
- [x] T044 [FR-002] [FR-003] [FR-007] [FR-008] [FR-015] Close demonstrated reference-analysis gaps in `packages/reality-core/src/reality/services/business_blueprint_analysis.py` and `business_blueprint_source.py` using live expressions; add failing regressions before each fix and never shrink `contracts/reference-boundary.md` to hide unresolved business decisions.
- [x] T045 [FR-005] [FR-010] [FR-014] [FR-018] [FR-019] Extend `packages/reality-core/tests/test_business_blueprint_release.py` and `apps/docs/scripts/business-blueprints.test.mjs` for complete packaged-source/test provenance, public admission/response caps, absent artifacts and mixed-release rollback; document tested configuration in `specs/343-business-logic-blueprints/quickstart.md`.
- [x] T046 [FR-010] [FR-011] [FR-014] [FR-017] [FR-018] [FR-019] Document durable live-source, test-evidence and public/private boundaries in `docs/features/business-logic-blueprints.md`, `docs/ARCHITECTURE.md`, `docs/WEB_SPEC.md` and `docs/TEST_STRATEGY.md`; preserve unrelated existing edits and record rollout/rollback without generated current explanations.
- [ ] T047 [FR-001] [FR-002] [FR-003] [FR-015] Conduct the five-minute ERP-professional understanding exercise and record reviewer observations, reference-boundary denominator and all uncovered aspects in `specs/343-business-logic-blueprints/verification.md`; do not invent review participation or mark this task complete from agent self-review.
- [x] T048 Run `make spec-check`, `make lint`, complete PostgreSQL `make test`, `make web-build`, the frontend i18n audit, registered browser suite, docs tests/live-docs browser check, `make docs-generate`, `make docs-catalog-check`, `make docs-build` and API/MCP image evidence smoke checks; record actual results and baseline blockers separately in `specs/343-business-logic-blueprints/verification.md`.
- [x] T049 Review the final diff against every FR/DR, source disclosure boundary, no-schema/no-job design and rollback; update `specs/343-business-logic-blueprints/verification.md`, `quickstart.md` and task state only when required proofs are green, without committing unrelated work or changing reviewer-owned checklist markers.

## Implementation path notes

The implementation keeps registered root resolution in `services/business_blueprints.py` rather than changing existing catalog behavior. Test parsing is isolated in `services/business_blueprint_tests.py`, shared by the orchestration service. The Web and docs presentations use `apps/shared/businessBlueprint.ts` plus `LiveBusinessBlueprint.tsx` / `LiveBusinessBlueprint.vue`; existing `CatalogCodeDialog.tsx` remains compatible and versioned snapshots are displayed inside the live component. Optional trusted run records are read from the release-owned raw-evidence manifest, with exact test/source digest binding; absent records remain unknown.

Automated gates and implementation tasks are checked against the executed evidence in verification.md. T047 requires a real ERP-professional participant; T034 retains the live natural-language cross-surface review. T033 vocabulary is regenerated, while its commit step remains pending in the shared dirty worktree. No unrelated changes are committed.

## Dependencies and implementation strategy

1. T001–T003 gates → T004–T009 source foundation → US1 T010–T020.
2. US2 T021–T027 depends on foundation and US1 rule graph; it remains independently usable without US3/US4.
3. US3 T028–T034 depends on US1 and US2 shared outputs; Chat/MCP do not implement a second analyzer.
4. US4 T035–T042 depends on US2 comparable conditions; its structured service tests do not require a model provider. Adapter tool registration follows US3.
5. T043 is written before T044 completes reference acceptance; it checks the integrated graph built in preceding phases, not a mirrored implementation.
6. T043–T049 verify the complete release; this sequence does not authorize deployment or merge.

**MVP**: Foundation + US1 provides useful source-backed operational inspection. It is an intermediate increment, not completion of the requested feature. The first acceptable full release includes US2–US4 and every final gate, especially the live-source reference journey.

**Parallel examples** (optional execution opportunities, not delegated-agent instructions):

- Foundation: T004 release proof and T005 response/identity proof touch different test files.
- US1: T010 inventory, T012 adapter and T013 browser proofs can be authored independently once source contracts exist; T011 follows T005 in the shared analysis test file.
- US2: T021/T022 share a test file and are sequential; T023 browser proof can run in parallel before T024–T026.
- US3: T028 adapter proofs and T029 docs proofs are independent; T030 precedes T031, and docs rendering consumes the settled shared contract.
- US4: T035 case proofs and T037 browser proofs are independent; T036 follows earlier adapter-test edits. Shared service/UI files are edited sequentially.

## Requirement Coverage

Each row includes test tasks before the relevant implementation. Verification/review tasks supplement, rather than replace, executable proof.

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T010 | T014, T017, T033 | Automated evidence recorded |
| FR-002 | T011, T043 | T016, T017, T044 | Automated evidence recorded |
| FR-003 | T011, T013, T043 | T016, T019, T032, T044 | Automated evidence recorded |
| FR-004 | T005, T010 | T006, T014, T015 | Automated evidence recorded |
| FR-005 | T004, T012, T013 | T007, T008, T017–T019 | Automated evidence recorded |
| FR-006 | T004, T011 | T006, T007, T016, T017 | Automated evidence recorded |
| FR-007 | T021, T023, T043 | T008, T024, T026, T044 | Automated evidence recorded |
| FR-008 | T021, T022, T023, T043 | T024–T026, T044 | Automated evidence recorded |
| FR-009 | T022, T023 | T006, T025, T026 | Automated evidence recorded |
| FR-010 | T013, T023, T028, T029 | T018, T019, T026, T032, T033 | Automated evidence recorded |
| FR-011 | T028, T036 | T030, T031, T040 | Automated evidence recorded |
| FR-012 | T035–T037 | T038, T040, T041 | Automated evidence recorded |
| FR-013 | T035, T037 | T039–T041 | Automated evidence recorded |
| FR-014 | T004, T012, T028, T035, T036 | T007, T017, T018, T030, T039, T040 | Automated evidence recorded |
| FR-015 | T043 | T002, T015, T044; T047 professional review | Automated evidence recorded; human review pending |
| FR-016 | T013, T021, T023, T028, T029, T037 | T019, T026, T031–T033, T041 | Automated evidence recorded |
| FR-017 | T004, T011, T021, T029 | T007, T016, T017, T024, T032 | Automated evidence recorded |
| FR-018 | T004, T012, T029, T045 | T007, T008, T017, T025, T032, T046 | Automated evidence recorded |
| FR-019 | T004, T011, T021, T029, T045 | T007, T008, T016, T017, T024, T032, T046 | Automated evidence recorded |
| DR-001 | T035, T043 | T038, T039 | Automated evidence recorded |
| DR-002 | T035, T043 | T038, T039 | Automated evidence recorded |
| DR-003 | T012, T028, T035, T036 | T018, T030, T039, T040 | Automated evidence recorded |
| DR-004 | T005, T010 | T006, T014, T015, T038 | Automated evidence recorded |

## Success-criterion evidence

| Criterion | Task(s) | Evidence |
|---|---|---|
| SC-001 | T010, T014, T020 | All-public-entry denominator and missing statuses |
| SC-002 | T002, T043, T044 | Enumerated boundary, branches and actual tests/gaps |
| SC-003 | T047 | Documented ERP-professional review, not self-certification |
| SC-004 | T028, T029, T034 | Cross-surface same-release rule/scenario parity |
| SC-005 | T022, T035, T036, T045 | Evidence status fixtures and unauthorized reads |
| SC-006 | T003, T021, T027, T049 | Complete FR/DR mapping and assertion fidelity |
| SC-007 | T004, T011, T021, T029 | Loaded-release change without explanation generation |

## Reopened: ERP readability correction

- [x] T050 [FR-020] [FR-021] Add source-derived generic live LLM presentation and unknown-operation/source-change/citation/graph fidelity regression tests first in tests/test_business_blueprint_presentation.py.
- [x] T051 [FR-020] [FR-021] Add immutable response models and implement services/business_blueprint_presentation.py; integrate in the shared explain service with a generic structured-output deployment provider, without authored operation-specific prose or saved answers.
- [x] T052 [FR-022] Add actual test Given/When/Then summaries with unresolved assertion counts, original evidence and unknown execution retained.
- [x] T053 [FR-020] [FR-021] [FR-022] Render primary business view and localized tests in both live components; collapse technical analysis; retain source and comparison controls.
- [x] T054 [FR-020] [FR-021] [FR-022] Verify focused backend suites, frontend/docs tests/builds and actual live credit/item browser reads, record evidence and review all new FR mappings. Human ERP review T047 remains pending.

Correction analysis: FR-020 maps T050/T051/T053/T054; FR-021 maps T050/T051/T053/T054; FR-022 maps T052/T053/T054. No CRITICAL requirement/plan conflict or unresolved clarification. Existing no-provider constraint preserved. Partial business interpretation must be disclosed separately from source availability, and must not certify SC-003.

LLM correction analysis: T050/T051/T052/T054 additionally prove generic unseen-operation handling, prompt freshness, bounded inference, known citations, honest failure and source revalidation. Original no-provider plan restriction is explicitly superseded by the user-approved presentation-only LLM integration. All FR mappings remain intact; zero CRITICAL unresolved conflicts.

## Loading and responsive flow correction

- [x] T055 [FR-023] [FR-024] Add delayed-read and long-text/mobile flow browser regressions in apps/docs/scripts/business-blueprints-browser.mjs and rendered branch fidelity proof in apps/docs/scripts/business-blueprints.test.mjs.
- [x] T056 [FR-023] [FR-024] Implement shared response-only flowCards and accessible timed waiting state in both live adapters.
- [x] T057 [FR-023] [FR-024] Verify adapter tests/builds and desktop/mobile browser screenshots; record visual review and remaining semantic-review limitations.

Analysis: user screenshots establish approved correction scope; FR-023 maps T055–T057, FR-024 maps T055–T057. No unresolved clarification, no CRITICAL conflicts, no domain/schema changes. Existing reviewer-owned checklist remains unchanged under prior authorization to continue.

- [x] T058 [FR-025] Test and implement brief initial reads plus explicit full-read controls; measure actual live latency and retain source/test freshness. Analysis: FR-025 maps T058; user explicitly requests latency correction, no critical conflicts or unresolved product choices.

T058 implements and measures the brief path; the 3–5s performance target is explicitly NOT certified. Final runs vary, and T047 human/semantic review remains pending.

- [x] T059 [FR-011] Reproduce actual Chat tool routing; test and implement generic wrong-kind recovery in shared discovery and evidence-only Chat guidance; verify actual Chat/MCP explain and existing adapter parity. Analysis: restores specified shared evidence access, mapped tests first, no critical consistency findings or unresolved clarification.

- [x] T060 [FR-026] Add source-span regression tests, shared local helpers and focused escaped source components in Docs/Inspector.
- [x] T061 [FR-027] Apply UX-reviewed three-area hierarchy, numbered rule cards and selectable test-case panels with existing comparison behavior.
- [x] T062 [FR-026] [FR-027] Verify keyboard/local navigation, exact source marking, refresh isolation and desktop/mobile visual screenshots; run adapter tests/builds and record review.

UX correction analysis: FR-026 maps T060/T062; FR-027 maps T061/T062. Scope approved by user screenshots/instruction; UX review complete, zero unresolved clarifications or critical conflicts. Reviewer-owned checklists remain unchanged under existing authorization.

- [x] T063 [FR-028] Test and implement generic multiline IF/THEN/ELSE step guidance, remove the duplicate business flow view and verify both reading adapters without inventing branches.

- [x] T064 [FR-029] Test and implement localized ordered object navigation, catalog-backed read-only starter links and concise intro; verify actual Docs navigation and mobile sizing with tests/build.

- [x] T065 [FR-027] Restore technical-detail segregation for the Docs API server address: show an explanatory live-read hint in the primary view, retain the address only in technical evidence and verify the initial-render regression.

- [x] T066 [FR-030] Test and implement intuitive Docs explanation entry and secondary refresh hierarchy; verify rendered states, browser loading/freshness/retry and Docs build.

- [x] T067 [FR-031] Test and implement business-first detail title/purpose, inline explanation action and optional catalog purpose translations; regenerate reference data and verify Docs tests/build/browser layout.

- [x] T068 [FR-032] Test and implement direct source-only Docs entry plus registered exception coverage and shared-evaluator disclosure; verify Docs/backend/browser checks and update the PR.

- [x] T069 [FR-035] Add regression tests first; audit all view/projection evidence and root availability, retain true reader/builders with shared-scope disclosure, render original source line numbers, improve error reporting, and verify backend/Docs/browser checks before updating the PR.

- [x] T070 [FR-036] Test and implement verified fixed projection binding for shared Chat/MCP source reads; compare adapter source digests, verify generic future names and dynamic-binding rejection, run feature checks and update PR.

- [x] T071 [FR-037] Preserve original code rows with compact typography and contained horizontal scrolling; verify Docs tests/build and browser dimensions, then update PR.

- [x] T072 [FR-038] Add lazy Python syntax colors for inspected source functions with safe escaped token spans, test exact text/color/fallback in browser, verify Docs tests/build and update PR.

- [x] T075 [FR-039] Test and implement the four-section Docs inspector with lazy evidence, local reuse and correct invalidation; place catalog reference in Technical details, preserve unsupported entries, and verify SSR/browser/build checks before updating PR.

- [x] T076 [FR-040] Apply scoped detail typography and narrow-screen section navigation; verify Docs tests, build and browser layout.
