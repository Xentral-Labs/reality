---
description: "Requirement-traceable product documentation implementation tasks"
---

# Tasks: Product Documentation Surface

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/documentation-surface.md`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All artifacts MUST be written in English. Tests precede the implementation they prove.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm approved requirements and absence of clarification markers in `specs/031-product-documentation/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/031-product-documentation/plan.md`
- [x] T003 Review documentation requirements quality in `specs/031-product-documentation/checklists/documentation.md`
- [x] T004 Run `$speckit-analyze` and resolve all CRITICAL findings across `specs/031-product-documentation/spec.md`, `plan.md`, and `tasks.md`

## Phase 2: Setup and Failing Proof

- [x] T005 Create Docs package manifest, formatter configuration, and source folders in `apps/docs/package.json`, `apps/docs/.prettierrc.json`, and `apps/docs/.prettierignore`
- [x] T006 [FR-001] [FR-002] [FR-011] [FR-018] Add failing content, navigation, search, and internal-link contract assertions in `apps/docs/scripts/docs-contract.test.mjs`
- [x] T007 [P] [FR-014] [FR-015] [FR-018] Add failing container, health-route, and Compose independence assertions in `apps/docs/scripts/docs-deployment.test.mjs`
- [x] T008 [P] [FR-016] [FR-017] [SC-006] Add failing cross-surface `DOCS_URL` preservation assertions in `apps/docs/scripts/docs-deployment.test.mjs`

## Phase 3: User Story 1 — Understand Reality (P1) 🎯 MVP

**Goal**: Readers understand Reality and its canonical traceability model.

**Independent Test**: Open Docs home and reach Getting Started, the canonical model, glossary, and Product Web in no more than three navigation choices.

- [x] T009 [US1] [FR-001] [FR-002] [FR-011] [SC-001] Configure home, navigation, outlines, next/previous links, and local search in `apps/docs/.vitepress/config.mts`
- [x] T010 [P] [US1] [FR-001] [FR-003] [SC-001] Author the product introduction and first traceable journey in `apps/docs/content/index.md` and `apps/docs/content/getting-started/index.md`
- [x] T011 [P] [US1] [FR-004] [DR-001] [DR-002] Author the canonical Source → Evidence → Reality explanation in `apps/docs/content/concepts/index.md` and `apps/docs/content/concepts/reality-model.md`
- [x] T012 [P] [US1] [FR-010] [DR-001] [DR-002] Author canonical terminology in `apps/docs/content/reference/glossary.md`
- [x] T013 [US1] [FR-012] [FR-019] [FR-020] Add Reality visual identity, responsive layout, visible focus, and claim-callout styles in `apps/docs/.vitepress/theme/index.ts` and `apps/docs/.vitepress/theme/custom.css`
- [x] T014 [US1] [FR-001–FR-004] [DR-001–DR-002] Run the US1 contract slice with `npm test -- --test-name-pattern="content|navigation|concept"` in `apps/docs`

## Phase 4: User Story 2 — Complete a Product Task (P2)

**Goal**: Operators and integrators find and follow accurate task-oriented guidance.

**Independent Test**: Search for a representative task, complete one guide, identify prerequisites and expected outcome, and recover from no results or an unknown route.

- [x] T015 [P] [US2] [FR-005] [DR-003] Author Operations Cockpit, Inspector, Activity, Ask Reality, sources, exceptions, traceability, and preferences guidance in `apps/docs/content/product-guides/index.md` and `apps/docs/content/product-guides/surfaces.md`
- [x] T016 [P] [US2] [FR-006] [DR-001] [DR-003] Author connector, import, lossless payload, idempotency, mapping, and recovery guidance in `apps/docs/content/integrations/index.md` and `apps/docs/content/integrations/connector-contract.md`
- [x] T017 [P] [US2] [FR-007] [DR-003] Author authentication, tenant context, OpenAPI, interface parity, and supported example guidance in `apps/docs/content/api-tools/index.md`
- [x] T018 [US2] [FR-011] [FR-013] Configure local search and useful not-found recovery in `apps/docs/.vitepress/config.mts` and `apps/docs/content/404.md`
- [x] T019 [US2] [FR-005–FR-007] [FR-011–FR-013] [DR-003] Run the US2 contract and production-build slices in `apps/docs`

## Phase 5: User Story 3 — Deploy and Maintain Reality (P3)

**Goal**: Contributors can build, deploy, operate, and govern Docs independently.

**Independent Test**: A clean install builds Docs; its container serves root and health without other services; CI detects missing content, links, or URL contracts.

- [x] T020 [P] [US3] [FR-008] [FR-014] Author container, PostgreSQL, migrations, backup/restore, health, logs, Railway, upgrade, rollback, security, and readiness guidance in `apps/docs/content/operations/index.md` and `apps/docs/content/operations/deployment.md`
- [x] T021 [P] [US3] [FR-009] [DR-003] Author repository, Spec Kit, Constitution, testing, domain-first, connector, and contribution guidance in `apps/docs/content/development/index.md`
- [x] T022 [P] [US3] [FR-010] [FR-016] Author environment, architecture/data-flow, versioning, and canonical-contract references in `apps/docs/content/reference/index.md` and `apps/docs/content/reference/environment.md`
- [x] T023 [US3] [FR-014] [FR-018] Add multi-stage static container and health routing in `apps/docs/Dockerfile` and `apps/docs/nginx.conf`
- [x] T024 [US3] [FR-015] [FR-016] Add independent Docs service and local development mount in `compose.yml` and `compose.dev.yml`
- [x] T025 [US3] [FR-016] [FR-017] Wire build-time `DOCS_URL` without renaming existing origins in `provider-site/Dockerfile`, `provider-site/vite.config.ts`, `provider-site/src/vite-env.d.ts`, `apps/web/Dockerfile`, `apps/web/vite.config.ts`, and `apps/web/src/vite-env.d.ts`
- [x] T026 [US3] [FR-017] Add Docs links using normalized `DOCS_URL`, including a new-tab company-menu link, in `provider-site/src/components/PublicHeader.tsx` and `apps/web/src/App.tsx`
- [x] T027 [US3] [FR-018] Add `docs-build` and dedicated Docs CI quality gate in `Makefile` and `.github/workflows/quality.yml`
- [x] T028 [US3] [FR-015–FR-020] Update runtime, URL, content, and rollback contracts in `README.md` and `docs/WEB_SPEC.md`
- [x] T029 [US3] [FR-014–FR-018] Run Docs build, deployment contracts, Compose validation, and container smoke scenario from `specs/031-product-documentation/quickstart.md`

## Final Phase: Cross-Cutting Review

- [x] T030 [FR-001–FR-020] [DR-001–DR-003] Run requirement and internal-link coverage through `apps/docs/scripts/docs-contract.test.mjs`
- [x] T031 Run `python3 scripts/check_spec_policy.py` and review feature artifacts in `specs/031-product-documentation/`
- [x] T032 Run backend lint/tests plus Site, Web, and Docs quality gates from `Makefile`
- [x] T033 [US3] [FR-016] [FR-017a] Add a failing Docs outbound-link configuration contract, pass `APP_URL` and `SITE_URL` into the Docs image build, replace the hard-coded home action through VitePress page-data transformation, build with alternate origins, and verify the generated output
- [x] T033 Review no-schema migration and independent-service rollback statements in `specs/031-product-documentation/plan.md`
- [x] T034 Review final diff against Constitution, `docs/WEB_SPEC.md`, and every FR/DR
- [x] T035 Record validation evidence in `specs/031-product-documentation/quickstart.md` and mark implementation tasks complete only after gates are green
- [x] T036 [US3] [FR-017] Move the public Site documentation destination from primary navigation to the responsive landing footer and add a regression contract
- [x] T037 [US3] [FR-017] Group Documentation and Reality website as secure external Resources in the Product Web company menu and add regression coverage

## Dependencies & Execution Order

- Phase 1 blocks implementation and must pass before Phase 2.
- Phase 2 establishes failing proofs and package structure before content or runtime implementation.
- US1 is the MVP and establishes navigation/theme primitives.
- US2 depends on US1 navigation but its content pages are otherwise independently testable.
- US3 depends on a buildable Docs artifact; its content tasks T020–T022 can proceed in parallel.
- Final review depends on all selected stories.

## Parallel Opportunities

- T007 and T008 cover different assertion families but share one file and therefore execute sequentially when one author performs both.
- T010–T012 author separate content paths in parallel after T009.
- T015–T017 author independent content areas in parallel.
- T020–T022 author independent operations/development/reference areas in parallel.

## Requirement Coverage

| Requirement | Test/evidence task(s) | Implementation/content task(s) | Status |
|---|---|---|---|
| FR-001–FR-004 | T006, T014, T030 | T009–T013 | Complete |
| FR-005–FR-007 | T006, T019, T030 | T015–T017 | Complete |
| FR-008–FR-010 | T006, T029–T030 | T020–T022 | Complete |
| FR-011–FR-013 | T006, T019, T030 | T009, T013, T018 | Complete |
| FR-014–FR-018 | T007–T008, T029–T030 | T023–T028 | Complete |
| FR-019–FR-020 | T006, T030–T032 | T013, T015–T022, T028 | Complete |
| DR-001–DR-002 | T014, T030 | T011–T012 | Complete |
| DR-003 | T019, T030 | T015–T017, T021 | Complete |
| SC-001–SC-007 | T014, T019, T029–T032 | T009–T028 | Complete |

## Implementation Strategy

The MVP is US1 after setup: a deployable information architecture is not yet required, but the Docs project can build and readers can understand the core model. US2 adds practical adoption value. US3 makes the surface operationally independent and merge-ready.
