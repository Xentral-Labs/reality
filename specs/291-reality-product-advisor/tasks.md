---
description: "Requirement-traceable Reality Product Advisor implementation tasks"
---

# Tasks: Reality Product Advisor

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/product-advisor-api.md`, `quickstart.md`
**Gate**: Constitution Check passed, no unresolved `[NEEDS CLARIFICATION]`, and reviewer-owned checklist disposition recorded before implementation

All artifacts MUST be written in English. Tests precede the behavior they prove.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner scope approval and record the specification reviewer/date in `specs/291-reality-product-advisor/checklists/advisor-review.md`
- [x] T002 Confirm every Constitution Check row and architecture review disposition in `specs/291-reality-product-advisor/plan.md` and `specs/291-reality-product-advisor/checklists/advisor-review.md`
- [x] T003 Run `$speckit-analyze`, resolve every CRITICAL/HIGH finding in `specs/291-reality-product-advisor/`, and record the clean result in `specs/291-reality-product-advisor/quickstart.md`

## Phase 2: Foundational Source and Domain Contracts

- [x] T004 [P] [FR-005] [FR-006] [FR-007] Add failing source-eligibility, visibility and authority tests in `packages/reality-core/tests/test_product_advisor_knowledge.py`
- [x] T005 [P] [FR-021] [FR-022] [FR-023] Add failing generation, duplicate, broken-reference, stale-source and leakage tests in `apps/docs/scripts/test_product_advisor_reference.py`
- [x] T006 [P] [FR-008] [FR-008a] [FR-009] [DR-001] [DR-002] [DR-005] [DR-007] Add failing immutable evidence, material-claim coverage and knowledge-version rule tests in `packages/reality-core/tests/test_product_advisor_claims.py`
- [x] T007 [FR-005] [FR-006] [FR-007] Define reviewed source classes and the initial durable-document allowlist in `packages/reality-core/config/product_advisor_sources.yaml`
- [x] T008 [FR-008] [FR-008a] [FR-009] [DR-001] [DR-002] [DR-005] [DR-007] Implement immutable evidence, material-claim coverage, question, answer and version rules in `packages/reality-core/src/reality/domain/product_advisor.py`
- [x] T009 [FR-021] [FR-022] [FR-023] Implement deterministic extraction and validation in `apps/docs/scripts/generate-product-advisor-knowledge.py`
- [x] T010 [FR-021] [FR-022] Generate and commit the deterministic artifact at `packages/reality-core/config/product_advisor_knowledge.json`
- [x] T011 [FR-005] [FR-006] [FR-007] [FR-021] Document source eligibility and review ownership in `docs/features/business-journey-guide.md`

## Phase 3: User Story 1 — Researched capability answer (P1)

**Independent test**: Ask about under-delivery, three-way matching, blanket orders and credit limits; no claim exceeds its exact evidence.

- [x] T012 [P] [US1] [FR-002] [FR-004] Add failing classification and bounded retrieval tests in `packages/reality-core/tests/test_product_advisor_service.py`
- [x] T013 [P] [US1] [FR-008] [FR-009] [FR-010] [FR-011] Add failing migration, automatic-credit-hold, return-end-to-end and adjacent-primitive regressions in `packages/reality-core/tests/test_product_advisor_claims.py`
- [x] T014 [P] [US1] [FR-012] [FR-014] [FR-015] Add failing answer-structure and governed-tool-mode tests in `packages/reality-core/tests/test_product_advisor_service.py`
- [x] T015 [US1] [FR-002] [FR-004] Implement intent classification, aliases and bounded per-concern retrieval in `packages/reality-core/src/reality/services/product_advisor.py`
- [x] T016 [US1] [FR-008] [FR-009] [FR-010] [FR-011] Implement claim drafting, support ceilings, limitation preservation and prohibited-transition validation in `packages/reality-core/src/reality/services/product_advisor.py`
- [x] T017 [US1] [FR-012] [FR-014] [FR-015] Implement validated composition and governed tool selection in `packages/reality-core/src/reality/services/product_advisor.py`
- [x] T018 [US1] [FR-020] Implement deterministic narrow-question and provider-failure fallback in `packages/reality-core/src/reality/services/product_advisor.py`
- [x] T019 [US1] [FR-027] Preserve Journey search, proposal and voting behavior while delegating answers in `packages/reality-core/src/reality/services/business_journeys.py`

## Phase 4: User Story 2 — Broad solution advice (P1)

**Independent test**: Ask for B2B sales covering prices, credit limits, partial delivery, collective invoicing and returns; requested concerns and material gaps are present.

- [x] T020 [P] [US2] [FR-003] [FR-013] Add failing decomposition, interpretation and single-clarification tests in `packages/reality-core/tests/test_product_advisor_service.py`
- [x] T021 [P] [US2] [FR-011] [FR-014] Add failing native/manual/agent-proposal/workaround/gap cases in `packages/reality-core/tests/test_product_advisor_claims.py`
- [x] T022 [P] [US2] [FR-012] Add failing concise-workflow and anti-catalog-dump cases in `packages/reality-core/tests/fixtures/product_advisor_buyer_cases.yaml`
- [x] T023 [US2] [FR-003] Implement bounded subquestion planning and per-concern coverage in `packages/reality-core/src/reality/services/product_advisor.py`
- [x] T024 [US2] [FR-013] Implement explicit interpretation and one-question clarification in `packages/reality-core/src/reality/services/product_advisor.py`
- [x] T025 [US2] [FR-011] [FR-012] [FR-014] Implement broad workflow assembly with required material gaps in `packages/reality-core/src/reality/services/product_advisor.py`

## Phase 5: User Story 3 — Product, technical and multilingual evaluation (P1)

**Independent test**: Ask about integrations, migration, chat scope and tenancy in English, German, Dutch, Spanish, French, Polish, Turkish, Arabic and Japanese; conclusions remain equal and answers use the detected language.

- [x] T026 [P] [US3] [FR-005] [FR-006] [FR-007] Add failing technical-contract retrieval and code/plan exclusion cases in `packages/reality-core/tests/test_product_advisor_knowledge.py`
- [x] T027 [P] [US3] [FR-019] [FR-019a] Add failing detection, short-follow-up and surface-fallback cases in `packages/reality-core/tests/test_product_advisor_languages.py`
- [x] T028 [P] [US3] [FR-016] [FR-026] [DR-003] Add failing disclosure, source-scope, injection and diagnostic-boundary tests in `packages/reality-core/tests/test_product_advisor_security.py`
- [x] T029 [US3] [FR-005] [FR-006] [FR-007] Add reviewed technical contract sections to `packages/reality-core/config/product_advisor_sources.yaml` and regenerate `packages/reality-core/config/product_advisor_knowledge.json`
- [x] T030 [US3] [FR-019] [FR-019a] Implement question-language detection and history/surface fallback in `packages/reality-core/src/reality/services/product_advisor.py`
- [x] T031 [US3] [FR-016] [FR-026] [DR-003] Implement public/internal scopes and bounded authorized diagnostics in `packages/reality-core/src/reality/services/product_advisor.py`
- [x] T032 [US3] [FR-010] Implement optional semantic review that can only reject or weaken claims in `packages/reality-core/src/reality/services/product_advisor.py`

## Phase 6: User Story 4 — One truth across all chat surfaces (P1)

**Independent test**: Ask equivalent public questions on every surface for one knowledge version, then continue with a scoped tenant follow-up.

- [x] T033 [P] [US4] [FR-001] [FR-018] Add failing compatible API and parity tests in `packages/reality-core/tests/test_business_journey_api.py`
- [x] T034 [P] [US4] [FR-001] [FR-018] [DR-004] Add failing read-tool parity and internal-ceiling tests in `packages/reality-core/tests/test_business_journey_tools.py`
- [x] T035 [P] [US4] [FR-017] [DR-003] [DR-006] Add failing product-intent, tenant-follow-up and confirmation Chat stories in `packages/reality-core/tests/test_chat_tools.py`
- [x] T036 [P] [US4] [FR-018] Add failing claims/sources compatibility tests in `apps/docs/scripts/business-journey-guide.test.mjs` and `apps/docs/scripts/business-journey-widget.test.mjs`
- [x] T037 [US4] [FR-001] [FR-018] Extend the additive transport in `packages/reality-core/src/reality/web/journey_guide_api.py`
- [x] T038 [US4] [FR-001] [FR-018] [DR-004] Route the canonical read tool through the Advisor in `packages/reality-core/src/reality/tools/business_journeys.py`
- [x] T039 [US4] [FR-017] [DR-003] [DR-006] Replace phrase-only routing while preserving tenant tools in `packages/reality-core/src/reality/services/core.py`
- [x] T040 [US4] [FR-018] Render returned claims and sources without status inference in `apps/docs/.vitepress/theme/components/BusinessJourneyGuide.vue`
- [x] T041 [US4] [FR-018] Render the additive response safely in `apps/docs/public/journey-guide-widget/widget.js`

## Phase 7: User Story 5 — Living knowledge and release evaluations (P1)

**Independent test**: Change a fixture source, remove a referenced tool and introduce an overclaim; valid changes update and unsafe/stale cases fail.

- [x] T042 [P] [US5] [FR-024] [FR-025] Build at least 75 reviewed buyer cases in `packages/reality-core/tests/fixtures/product_advisor_buyer_cases.yaml`
- [x] T043 [P] [US5] [FR-019] [FR-019a] [FR-024] Add equivalent English, German, Dutch, Spanish, French, Polish, Turkish, Arabic and Japanese questions to `packages/reality-core/tests/fixtures/product_advisor_buyer_cases.yaml`
- [x] T044 [US5] [FR-024] [FR-025] Implement required/forbidden-claim and source evaluation in `packages/reality-core/tests/test_product_advisor_evaluation.py`
- [x] T045 [US5] [FR-021] [FR-022] [FR-023] Add advisor generation and stale-output enforcement to `Makefile`
- [x] T046 [US5] [FR-021] [FR-022] [FR-023] Document contribution, review and remediation in `docs/features/business-journey-guide.md`
- [x] T047 [US5] [FR-026] Document authorized decision inspection and redaction in `docs/features/business-journey-guide.md`

## Final Phase: Cross-Cutting Verification and Review

- [x] T048 Run `make spec-check` and audit every FR/DR coverage row below
- [x] T049 Run `make lint` and the focused suites from `specs/291-reality-product-advisor/quickstart.md`
- [x] T050 Run the complete PostgreSQL backend suite with `make test`
- [x] T051 Run `make docs-catalog-check`, `make docs-build` and `make web-build`
- [x] T052 Execute and record the Website, Docs and authenticated Chat smoke matrix in `specs/291-reality-product-advisor/quickstart.md`
- [x] T053 Review the final diff against the Constitution, source allowlist, tenant/confirmation boundaries and rollback in `specs/291-reality-product-advisor/plan.md`
- [ ] T054 Record specification, architecture and final reviewer decisions in `specs/291-reality-product-advisor/checklists/advisor-review.md`
- [ ] T055 Update `docs/V0_CHECKLIST.md` only for evidence whose required checks are green

## Dependencies and Parallel Opportunities

1. Phase 1 blocks implementation; Phase 2 blocks all stories; US1 blocks US2–US4.
2. US2 and US3 may proceed in parallel after US1. US4 depends on both. US5 case authoring may begin after US1 but its release gate depends on US2–US4.
3. Parallel failing proofs: T004–T006, T012–T014, T020–T022, T026–T028 and T033–T036.

## Implementation Strategy

**MVP**: Phases 1–3 provide safer narrow answers, multi-source evidence, claim validation and deterministic fallback without breaking existing clients. Then add broad advice, technical/multilingual coverage, shared-surface rollout and the full release evaluation incrementally.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) |
|---|---|---|
| FR-001–FR-004 | T012, T020, T033–T034 | T015, T023, T037–T038 |
| FR-005–FR-007 | T004, T026 | T007, T011, T029 |
| FR-008–FR-008a, FR-009–FR-011 | T006, T013, T021 | T008, T016, T032 |
| FR-012–FR-015 | T014, T020–T022 | T017, T024–T025 |
| FR-016–FR-018 | T028, T033–T036 | T031, T037–T041 |
| FR-019–FR-019a | T027, T043 | T030 |
| FR-020 | T013 | T018 |
| FR-021–FR-023 | T005 | T009–T011, T045–T046 |
| FR-024–FR-025 | T042–T044 | T044 |
| FR-026–FR-027 | T028, T033–T036 | T019, T031, T047 |
| DR-001–DR-002 | T006, T035 | T008, T025 |
| DR-003–DR-004 | T028, T034–T035 | T031, T038–T039 |
| DR-005–DR-007 | T006, T028, T035 | T008–T010, T031, T039 |

## Phase 9: Convergence

- [x] T056 [US1] [FR-010] [FR-012] Add a regression test proving the provider prompt communicates every accepted workflow role and prevents valid researched answers from falling back because of an invented role
- [ ] T057 [US1] [FR-010] [FR-012] Align the provider output contract with the validated advisory claim schema and verify representative English and German ERP-buyer answers through the live local endpoint and widget (partial)
- [x] T058 [US2] [FR-013] Add regressions proving an unqualified partial-delivery question asks one customer-versus-supplier clarification and bounded B2B history does not silently resolve it
- [x] T059 [US1] [FR-012] Separate customer and supplier partial-delivery retrieval vocabulary, replace tautological A04/H02 public evidence with concrete quantity outcomes, regenerate advisory knowledge, and verify focused service/evaluation/security tests
- [x] T060 [US2] [FR-013] Add provider-contract regressions for clarification-only responses, general business-term ambiguity, direct answers for immaterial missing detail, and bounded-history handling
- [x] T061 [US2] [FR-013] Replace the partial-delivery phrase exception with the provider's general semantic ambiguity decision while retaining deterministic validation of one focused question and zero unsupported claims
- [x] T062 [US2] [FR-013] Run focused advisor tests, static checks, Spec Kit analysis and the required repository quality gates
