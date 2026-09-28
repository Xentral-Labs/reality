---
description: "Requirement-traceable Business Journey Guide implementation tasks"
---

# Tasks: Business Journey Guide

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/guide.md`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner scope/name decision and close clarification markers in `specs/290-business-journey-guide/spec.md`
- [x] T002 Confirm all Constitution Check rows are PASS in `specs/290-business-journey-guide/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings across `specs/290-business-journey-guide/`

## Phase 2: Foundational Catalog Proof

- [x] T004 [P] [US5] [FR-019] Add failing 228-ID parity, schema and visibility tests in `packages/reality-core/tests/test_business_journey_catalog.py`
- [x] T005 [P] [US5] [FR-002] [FR-003] [FR-020] Add failing broken tool/demo/relation and status/evidence tests in `packages/reality-core/tests/test_business_journey_catalog.py`
- [x] T006 [P] [US5] [FR-021] Add failing generation/freshness contract tests in `apps/docs/scripts/business-journey-guide.test.mjs`
- [x] T007 [US5] [FR-019] Create the validated canonical catalog in `packages/reality-core/config/business_journey_catalog.yaml`
- [x] T008 [US5] [FR-019] Implement immutable catalog models/loaders and public/internal serializers in `packages/reality-core/src/reality/domain/business_journeys.py`
- [x] T009 [US5] [FR-021] Implement idempotent guide/Markdown/public-JSON generation in `apps/docs/scripts/generate-journey-guide.py`
- [x] T010 [US5] [FR-021] Integrate journey generation and freshness into `Makefile` and `apps/docs/scripts/docs-contract.test.mjs`

## Phase 3: User Story 1 — Complete Public Guide (P1)

- [x] T011 [P] [US1] [FR-001] Add failing complete-ID/filter/detail component tests in `apps/docs/scripts/business-journey-guide.test.mjs`
- [x] T012 [P] [US1] [FR-023] Add failing demo-versus-capability copy contracts in `apps/docs/scripts/docs-contract.test.mjs`
- [x] T013 [US1] [FR-001] Build the filterable accessible guide component in `apps/docs/.vitepress/theme/components/BusinessJourneyGuide.vue`
- [x] T014 [US1] [FR-005] Add English and German guide entries in `apps/docs/content/getting-started/business-journeys.md` and `apps/docs/content/de/getting-started/business-journeys.md`
- [x] T077 [P] [US1] [FR-002a] Add failing journey-specific-limitation and no-repository-detail tests in `packages/reality-core/tests/test_business_journey_catalog.py`
- [x] T078 [US1] [FR-002a] Replace the generic limitation of all 74 missing, 81 partial and 3 out-of-scope journeys with the reason from `docs/scenarios/coverage.md`, rewritten for public readers, in `packages/reality-core/config/business_journey_catalog.yaml`
- [ ] T015 [US1] [FR-004] Link public tools, demo references, limitations and related journeys in `apps/docs/.vitepress/theme/components/BusinessJourneyGuide.vue`
- [x] T016 [US1] [FR-022] Add localized sidebar labels/routes without the reserved name in `apps/docs/.vitepress/config.mts`
- [x] T017 [US1] [DR-001] Add Source → Evidence → Reality explanation and capability-status definitions in `docs/features/business-journey-guide.md`
- [x] T018 [US1] [SC-001] Run the independent 228-entry browse/filter acceptance and record evidence in `specs/290-business-journey-guide/quickstart.md`

## Phase 4: User Story 2 — Grounded Questions (P1)

- [x] T019 [P] [US2] [FR-006] [FR-007] [DR-004] Add failing deterministic match/citation/status-ceiling tests in `packages/reality-core/tests/test_business_journey_questions.py`
- [x] T020 [P] [US2] [FR-009] Add failing English/German and multi-journey question matrix in `packages/reality-core/tests/fixtures/business_journey_questions.yaml`
- [x] T021 [P] [US2] [FR-010] Add failing adversarial/provider-timeout/invalid-citation API tests in `packages/reality-core/tests/test_business_journey_api.py`
- [x] T022 [US2] [FR-006] Implement deterministic ranking and structured cited answers in `packages/reality-core/src/reality/services/business_journeys.py`
- [x] T023 [US2] [FR-010] Add optional constrained provider rewrite with deterministic fallback in `packages/reality-core/src/reality/services/business_journeys.py`
- [x] T024 [US2] [FR-008] Expose bounded anonymous read endpoints in `packages/reality-core/src/reality/web/journey_guide_api.py` and register them in `packages/reality-core/src/reality/web/app.py`
- [x] T025 [US2] [FR-006] Add Ask Reality with cited local fallback/API enhancement in `apps/docs/.vitepress/theme/components/BusinessJourneyGuide.vue`
- [x] T026 [P] [US2] [FR-010a] Add failing launcher/dialog/mobile/keyboard/failure contracts in `apps/docs/scripts/business-journey-widget.test.mjs`
- [x] T027 [US2] [FR-010a] Build the framework-neutral public chatbot artifact in `apps/docs/public/journey-guide-widget/` and standalone fallback page in `apps/docs/content/getting-started/business-journey-chat.md`
- [x] T028 [US2] [FR-010b] Document and test the private marketing-site embed contract in `docs/features/business-journey-guide.md` and `apps/docs/scripts/business-journey-widget.test.mjs`
- [x] T029 [P] [US2] [FR-010c] Add failing normal-Chat capability-intent and status/citation parity tests in `packages/reality-core/tests/test_business_journey_questions.py`
- [x] T030 [US2] [FR-010c] Register guide query as a read tool in `packages/reality-core/src/reality/tools/business_journeys.py` and route capability questions through it in `packages/reality-core/src/reality/services/core.py`
- [x] T031 [US2] [FR-010d] Run Website-widget/Docs/normal-Chat parity and fallback acceptance and record repository plus external rollout evidence status in `specs/290-business-journey-guide/quickstart.md`

## Phase 5: User Story 3 — Internal Evidence (P2)

- [x] T032 [P] [US3] [FR-011] Add failing authorization/same-conclusion tests in `packages/reality-core/tests/test_business_journey_api.py`
- [x] T033 [P] [US3] [FR-012] Add failing public artifact/reply leakage scan in `packages/reality-core/tests/test_business_journey_catalog.py`
- [x] T034 [US3] [FR-011] Implement authorized internal evidence queries in `packages/reality-core/src/reality/services/business_journeys.py`
- [x] T035 [US3] [FR-011] Expose the internal account endpoint in `packages/reality-core/src/reality/web/journey_guide_api.py`
- [x] T036 [US3] [DR-005] Extend the shared Chat guide tool with authorized evidence in `packages/reality-core/src/reality/tools/business_journeys.py` and the executable catalogs
- [x] T037 [US3] [FR-012] Regenerate tool documentation with `make docs-generate` and commit `apps/docs/content/tool-usage/` plus `apps/docs/.vitepress/data/tool-usage.json`

## Phase 6: User Story 4 — Suggestions and Votes (P2)

- [x] T038 [P] [US4] [FR-013] Add failing proposal validation/lifecycle tests in `packages/reality-core/tests/test_business_journey_proposals.py`
- [x] T039 [P] [US4] [FR-015] [DR-002] [DR-003] Add failing PostgreSQL retry/concurrency/reversible-vote story in `packages/reality-core/tests/test_business_journey_proposals.py`
- [x] T040 [P] [US4] [FR-017] Add failing account authorization/confirmation/API tests in `packages/reality-core/tests/test_business_journey_api.py`
- [x] T041 [P] [US4] [FR-014] Add failing curated duplicate-similarity cases in `packages/reality-core/tests/fixtures/business_journey_questions.yaml`
- [x] T042 [US4] [FR-013] Add proposal/vote models and constraints in `packages/reality-core/src/reality/db/models.py`
- [x] T043 [US4] [FR-015] Add the reversible additive migration in `packages/reality-core/alembic/versions/`
- [x] T044 [US4] [FR-013] [FR-016] Implement prepare/confirm/moderate/list services in `packages/reality-core/src/reality/services/business_journeys.py`
- [x] T045 [US4] [FR-015] Implement retry-safe vote/withdraw and derived counts in `packages/reality-core/src/reality/services/business_journeys.py`
- [x] T046 [US4] [FR-017] Expose account/public proposal endpoints in `packages/reality-core/src/reality/web/journey_guide_api.py`
- [x] T047 [US4] [DR-006] Register proposal/vote prepare-confirm tools in `packages/reality-core/src/reality/tools/business_journeys.py` and tool/resource catalogs
- [x] T048 [US4] [FR-014] Add typed API methods and authenticated proposal/vote UI in `apps/web/src/api.ts` and `apps/web/src/unified/JourneySuggestions.tsx`
- [x] T049 [US4] [FR-014] Add Docs-to-Product-Web suggestion handoff in `apps/docs/.vitepress/theme/components/BusinessJourneyGuide.vue`
- [ ] T050 [US4] [FR-018] Add localized privacy/moderation/roadmap wording in `apps/web/src/localization.tsx` and Docs content
- [x] T051 [US4] [SC-007] Run migration, confirmation, duplicate and concurrent-vote acceptance and record evidence in `specs/290-business-journey-guide/quickstart.md`

## Final Phase: Cross-Cutting Review

- [x] T059 [US2] [FR-009] [FR-009a] Add provider-selection, typo, off-topic and EN/DE/NL/ES contract tests before implementation
- [x] T060 [US2] [FR-009] [FR-009a] Implement catalog-bounded Anthropic semantic selection and multilingual answers with deterministic fallback
- [x] T061 [US2] [FR-010b] Verify the public widget and normal Chat share the validated capability-answer service
- [x] T062 [US2] [FR-010e] Add new-tab citation, desktop panel, mobile sheet, scroll and safe message-rendering widget contracts
- [x] T063 [US2] [FR-010e] [FR-010f] Redesign the public widget and verify it on the marketing-site embed
- [x] T064 [US2] [FR-010b] Add Docs same-service, loading, cited-answer and separate catalog-browse contracts
- [x] T065 [US2] [FR-010b] Redesign the Docs Guide question and catalog experience and verify the live page
- [x] T066 [US2] [FR-010g] Add bounded follow-up-history, broad-overview and no-persistence tests
- [x] T067 [US2] [FR-010g] Implement the catalog-grounded Capability Advisor across API and public widget
- [x] T068 [US2] [FR-010h] Use neutral composer prompts and describe confirmed agent-assisted mutations without person-only wording
- [x] T069 [US2] [FR-010i] Add human-readable solution-first answers and executable-catalog tool recommendations
- [x] T070 [US2] [FR-010j] Add localized empty-state questions and human-readable citation chips
- [x] T071 [US2] [FR-010k] Render safe advisor headings, paragraphs and workflow/tool bullet lists
- [x] T072 [US2] [FR-010l] Add immediate example-submit feedback and accessible reduced-motion loading indicator
- [x] T073 [US2] [FR-010m] Replace citation badges with a compact accessible source table
- [x] T074 [US2] [FR-010l] Bind example controls through the connected shadow root and add a regression check
- [x] T075 [US2] [FR-010n] Reduce the visible loading state to an accessible animated three-dot indicator
- [x] T076 [US2] [FR-010o] Position each new answer at its beginning while keeping the composer fixed

- [x] T052 Run `make spec-check` and requirement/task traceability audit for `specs/290-business-journey-guide/`
- [ ] T053 Run catalog generation/freshness and public leakage gates with `make docs-generate docs-catalog-check`
- [ ] T054 Run Ruff and the complete required PostgreSQL backend suite with `make lint test`
- [ ] T055 Run Docs/Product Web builds, browser contracts, accessibility and `apps/web` localization audit
- [x] T056 Review migration upgrade/downgrade and deployment rollback described in `specs/290-business-journey-guide/plan.md`
- [ ] T057 Review final diff against Constitution, all FR/DR requirements and shortest true links
- [ ] T058 Update `docs/SPEC_COVERAGE_MATRIX.md`, durable contracts and task status only after required checks are green

## Dependencies

- Phase 2 blocks every story.
- US1 and US2 are the public MVP; US2 depends on catalog serialization but not proposal persistence.
- US3 depends on the US2 query service.
- US4 depends on catalog matching but can otherwise proceed independently of Docs UI.
- Final gates depend on all selected story phases.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001–FR-005 | T004, T011–T012 | T007–T018 | Pending |
| FR-006–FR-010 | T019–T021 | T022–T026 | Pending |
| FR-011–FR-012 | T027–T028 | T029–T032 | Pending |
| FR-013–FR-018 | T033–T036 | T037–T046 | Pending |
| FR-019–FR-024 | T004–T006, T011–T012, T033 | T007–T018, T039–T045 | Pending |
| DR-001–DR-006 | T019, T027–T028, T034–T035 | T017, T022, T029–T031, T039–T042 | Pending |

## MVP

Phases 2–4 provide the independently releasable public guide and grounded question experience. Internal evidence and proposal voting remain separate follow-on increments, but the full feature is not complete until Phases 5–6 and final gates pass.
