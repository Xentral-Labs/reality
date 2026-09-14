---
description: "Requirement-traceable public-site and product-Web split tasks"
---

# Tasks: Separate Public Site and Product Web App

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede the implementation they prove.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm approved requirements and closed clarification markers in `specs/022-public-site/spec.md` and `specs/022-public-site/checklists/requirements.md`
- [x] T002 Confirm all Constitution Check rows are PASS in `specs/022-public-site/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL or HIGH findings across `spec.md`, `plan.md`, and `tasks.md`

## Phase 2: Failing Browser and Repository Proof

- [x] T004 [P] [US1] [FR-001] [FR-007] [FR-008] Add failing independent Site tree, link-origin, language, and no-API assertions, then move the owned contract to `provider-site/scripts/site-contract.test.mjs` during extraction
- [x] T005 [P] [US2] [FR-004] [FR-005] [FR-006] Add failing product-root and retired-landing-source assertions in `apps/web/scripts/product-boundary.test.mjs`
- [x] T006 [P] [US3] [FR-009] [FR-010] [FR-011] [FR-012] Add failing Site/Web Compose, CI, command, image, and documentation assertions in `packages/reality-core/tests/test_repository_layout.py`
- [x] T007 [P] [US1] [DR-001] [DR-002] [DR-003] Add failing static-boundary assertions proving Site has no API, auth-state, tenant, or business-module dependency, retained in `provider-site/scripts/site-contract.test.mjs`
- [x] T008 Run the new focused tests before extraction and record the expected red result in `specs/022-public-site/quickstart.md`

## Phase 3: User Story 1 — Canonical Public Site (P1)

**Goal**: Serve the existing landing experience from an independent static application.

**Independent Test**: Build and serve Site alone; verify root, language, account links,
and absence of API/application dependencies.

- [x] T009 [US1] [FR-001] Create locked Vite/React Site workspace and metadata in `provider-site/package.json`, `provider-site/package-lock.json`, `provider-site/tsconfig.json`, `provider-site/tsconfig.node.json`, and `provider-site/vite.config.ts`
- [x] T010 [US1] [FR-001] Move landing presentation into `provider-site/src/LandingPage.tsx`, `provider-site/src/landing.css`, `provider-site/src/main.tsx`, and `provider-site/index.html`
- [x] T011 [P] [US1] [FR-001] Add independently owned public presentation primitives in `provider-site/src/components/LogoMark.tsx`, `provider-site/src/localization.tsx`, and `provider-site/src/localization-core.ts`
- [x] T012 [US1] [FR-007] Implement normalized `APP_URL` account destinations with language preservation in `provider-site/src/LandingPage.tsx` and `provider-site/.env.example`
- [x] T013 [US1] [FR-008] Add static-only production ownership in `provider-site/Dockerfile`, `provider-site/nginx.conf`, and `provider-site/.dockerignore`
- [x] T014 [US1] [FR-002] [FR-003] Document canonical and `www` edge-routing contract in `specs/022-public-site/contracts/browser-origins.md` and `README.md`
- [x] T015 [US1] [DR-001] [DR-002] [DR-003] Run Site contract tests/build and record independent static evidence in `specs/022-public-site/quickstart.md`

## Phase 4: User Story 2 — Dedicated Product Application (P1)

**Goal**: Keep auth, onboarding, and ERP routes at the dedicated application origin.

**Independent Test**: Serve Product Web alone and verify root/auth/application behavior
without any landing-page source or route.

- [x] T016 [US2] [FR-004] [FR-005] Remove landing ownership from `apps/web/src/App.tsx`, `apps/web/src/LandingPage.tsx`, and `apps/web/src/landing.css`
- [x] T017 [US2] [FR-006] Make `apps/web/src/App.tsx` root use the existing `AuthGate` and authenticated product flow
- [x] T018 [US2] [FR-004] [FR-005] Remove retired marketing redirects and retain auth/application SPA routing in `apps/web/nginx.conf`
- [x] T019 [US2] [FR-005] Update product-boundary and localization source contracts in `apps/web/scripts/product-boundary.test.mjs`, `apps/web/scripts/i18n-audit.test.mjs`, and `apps/web/scripts/localization-contract.test.mjs`
- [x] T020 [US2] [FR-004] [FR-005] [FR-006] Run Product Web tests, audit, and build and record route evidence in `specs/022-public-site/quickstart.md`

## Phase 5: User Story 3 — Independent Development and Deployment (P2)

**Goal**: Make both browser applications explicit in local workflows, CI, Compose, and docs.

**Independent Test**: Follow clean-checkout commands and inspect independent Site/Web images and dependencies.

- [x] T021 [US3] [FR-009] Add separate Site install/test/audit/build and Product Web install/test/audit/build gates in `.github/workflows/quality.yml`
- [x] T022 [US3] [FR-009] [FR-010] Add `site-build` and updated Web commands in `Makefile`
- [x] T023 [US3] [FR-009] Update root Docker build exclusions for both browser applications in `.dockerignore`
- [x] T024 [US3] [FR-010] [FR-011] Add independent `site` service on port 8082 and retain `web` on 8080 with API-only dependency in `compose.yml`
- [x] T025 [US3] [FR-010] [FR-012] Update canonical production and local origins in `.env.example` and `README.md`
- [x] T026 [P] [US3] [FR-012] Update application ownership in `docs/ARCHITECTURE.md`, `docs/WEB_SPEC.md`, and `docs/decisions/0005-frontend-backend-object-storage.md`
- [x] T027 [P] [US3] [FR-012] Update future Spec Kit structure guidance in `.specify/templates/overrides/plan-template.md` and `.specify/templates/tasks-template.md`
- [x] T028 [US3] [FR-009] [FR-011] Update executable coverage ownership in `docs/SPEC_COVERAGE_MATRIX.md` and `packages/reality-core/tests/test_repository_layout.py`
- [x] T029 [US3] [FR-009] Install locked dependencies and run both browser test/audit/build command sequences from their own roots
- [x] T030 [US3] [FR-011] Validate Compose, build Site/Web images, and run independent lifecycle smoke tests

## Final Phase: Cross-Cutting Review

- [x] T031 [P] [FR-001] [FR-004] [FR-012] Scan active files for combined-site assumptions, relative public account links, and inconsistent domains
- [x] T032 [P] [FR-009] Run Spec Policy, repository layout tests, and Ruff using exact CI commands
- [x] T033 [DR-001] [DR-002] [DR-003] Run the full shared-core PostgreSQL suite and confirm no Alembic content or schema change
- [x] T034 [FR-001]–[FR-012] [DR-001]–[DR-003] Reconcile all acceptance and regression evidence with `specs/022-public-site/spec.md` and `specs/022-public-site/quickstart.md`
- [x] T035 Review rollback, final diff, Constitution compliance, and mark `specs/022-public-site/tasks.md` complete only after all gates are green
- [x] T036 [US3] [FR-009] Add root `make api`, `make app`, `make site`, and `make mcp` Compose start targets with executable repository-layout proof
- [x] T037 [US3] [FR-010] Add independent `API_PORT`, `APP_PORT`, `SITE_PORT`, and `MCP_PORT` Compose overrides and document URL-versus-port configuration
- [x] T038 [US3] [FR-012] Replace public `FRONTEND_URL`/`BACKEND_URL` configuration with uniform `APP_URL`/`API_URL`, keep framework-specific variables internal, and add regression proof
- [x] T039 [US3] [FR-013] Add failing repository proof for a separate source-mounted Site/Web/API/MCP reload stack in `packages/reality-core/tests/test_repository_layout.py`
- [x] T040 [US3] [FR-013] Implement `compose.dev.yml` with Vite hot reload, Uvicorn reload, source mounts, and isolated Node dependency volumes
- [x] T041 [US3] [FR-014] Add `make dev`, `make dev-up`, `make dev-logs`, `make dev-status`, and `make dev-down` lifecycle targets
- [x] T042 [US3] [FR-013] [FR-014] Document production-like versus development workflows and agent-readable logging in `README.md`
- [x] T043 [US3] [FR-013] [FR-014] Render the merged Compose configuration, smoke reload services, verify logs/status/teardown, and record evidence in `specs/022-public-site/quickstart.md`
- [x] T044 [US4] [FR-015] Add failing bilingual public-copy assertions that identify Reality as the shared agentic decision core in `provider-site/scripts/site-contract.test.mjs`
- [x] T045 [US4] [FR-015] Rewrite the hero proposition and add a responsive bring-your-agents operating-model section in `provider-site/src/LandingPage.tsx` and `provider-site/src/landing.css`
- [x] T046 [US4] [FR-015] Run the Site contract tests and production build and reconcile the new public positioning with the approved specification
- [x] T047 [US4] [FR-015] Add bilingual regression proof for the ERP, MCP, and Reality category distinction
- [x] T048 [US4] [FR-015] Add the missing-context chapter after source connection, renumber the following narrative, and verify the independent Site build
- [x] T049 [US4] [FR-015] Remove the redundant technical audit catalog so the public narrative ends after controlled delegation
- [x] T050 [US5] [FR-016] Add failing public contracts for the landing product overview and `/platform` operating-level route
- [x] T051 [US5] [FR-016] Add the responsive bilingual Observe, Operate, and Infrastructure overview to the landing narrative
- [x] T052 [US5] [FR-016] Implement the bilingual `/platform` page with invariant guarantees, level comparison, modules, deployment models, and account actions
- [x] T053 [US5] [FR-016] Run Site contracts and production build and reconcile the new product architecture with the approved specification
- [x] T054 [US5] [FR-016] Replace operating-maturity packages with concise Core, Scale, and Infrastructure capacity packages and failing bilingual contracts
- [x] T055 [US5] [FR-016] Simplify `/platform` to one three-column infrastructure comparison with explicit order, source, company, agent, history, and deployment allowances
- [x] T056 [US5] [FR-016] Add licensed self-hosted Infrastructure positioning and verify Site contracts and production build
- [x] T057 [US5] [FR-016] Reduce `/platform` to a GitLab-style pricing hierarchy with one heading, deployment tabs, and three concise capacity cards
- [x] T058 [US5] [FR-016] Refine the three-column comparison into a restrained enterprise infrastructure design with compact type hierarchy and equal card proportions
- [x] T059 [US5] [FR-016] Add a language-preserving Packages navigation link from the landing header to `/platform`
- [x] T060 [US5] [FR-016] Keep one identical four-item primary navigation across the landing and package pages
- [x] T061 [US5] [FR-016] Remove the inert deployment selector and place Packages last in the shared narrative navigation
- [x] T062 [US5] [FR-016] Replace volume-led Core and Scale tiers with integration-led Shopify, Business, and Infrastructure adoption packages across the landing and platform pages
- [x] T063 [US5] [FR-016] Replace the unavailable Infrastructure offer with a bounded 20-hour Consulting package across the landing and platform pages
- [x] T064 [US5] [FR-016] Replace fixed-hour Consulting with an individually scoped Enterprise offer and personal contact across the landing and platform pages
- [x] T065 [US5] [FR-016] Rename the entry package to Starter, limit it to three connected data sources, and position Business as the larger standard package
- [x] T066 [US5] [FR-016] Replace ambiguous Business Agent package terminology with explicit agent access credentials
- [x] T067 [US5] [FR-016] Reduce each package comparison from five technical rows to data sources, companies, and retained Reality history
- [x] T068 [US5] [FR-016] Add a compact Cloud versus self-hosted operating line with an official release-download destination
- [x] T069 [US5] [FR-016] Remove unverified daily order benchmarks and replace the dominant package value with concise outcome-led positioning
- [x] T070 [US6] [FR-017] Add failing bilingual Site contracts for the `/why-reality` education route and landing-page entry point
- [x] T071 [US6] [FR-017] Build the responsive category-education page with old-world comparison, conflicting order example, fact sequence, and durability explanation
- [x] T072 [US6] [FR-017] Add a language-preserving landing-page education link and verify Site contracts, build, Spec policy, and final diff
- [x] T073 [US6] [FR-017] Add concise Procurement and Finance conflicts during exploration; superseded by T086 to retain only Finance alongside the stronger fulfillment case
- [x] T074 [US6] [FR-017] Add one language-preserving Examples destination to the shared navigation on every public route
- [x] T075 [US6] [FR-018] Add a failing Site contract requiring every public route to use one shared, geometrically centered header and language control
- [x] T076 [US6] [FR-018] Extract the public header, preserve all language-aware destinations, and verify its desktop and responsive layout
- [x] T077 [US6] [FR-019] Add a failing bilingual Site contract for the recurring order story, flight-recorder analogy, and domain-specific agent outcomes
- [x] T078 [US6] [FR-019] Redesign `/why-reality` as a visual narrative with recurring business stories and a plain-language category explanation; superseded by T086 to focus the narrative
- [x] T079 [US6] [FR-019] Verify the expanded education narrative across Site contracts, production build, Spec policy, and final diff
- [x] T080 [US6] [FR-020] Add failing contracts for textbook-style definitions, worked reasoning, correction semantics, and category boundaries
- [x] T081 [US6] [FR-020] Expand `/why-reality` into a self-contained educational chapter with readable prose, definitions, derivation, and common questions
- [x] T082 [US6] [FR-020] Verify the long-form education chapter across Site contracts, production build, Spec policy, and final diff
- [x] T083 [US6] [FR-021] Add failing bilingual contracts for a realistic multi-record agent context packet and honest reconstruction comparison
- [x] T084 [US6] [FR-021] Add the fulfillment context case study with commitments, reservations, movements, constraints, lineage, and an actionable agent answer
- [x] T085 [US6] [FR-021] Verify the agent-context case study and update the open education PR
- [x] T086 [US6] [FR-017] [FR-019] Add failing focus assertions limiting education to the R-2087 fulfillment case and one concise Finance transfer example
- [x] T087 [US6] [FR-017] [FR-019] Remove the superseded R-1042 and Procurement scenarios and make R-2087 the single worked main example
- [x] T088 [US6] [FR-017] [FR-019] Verify the focused two-scenario education flow and update the open PR
- [x] T089 [US6] [FR-022] Add failing contracts for a chronological typed Reality graph and visible context selection
- [x] T090 [US6] [FR-022] Replace disconnected fulfillment cards with the human-readable and technically traceable record timeline
- [x] T091 [US6] [FR-022] Verify the timeline, responsive fallback, and updated open PR
- [x] T092 [US6] [FR-023] Add failing bilingual contracts for a branched temporal plan-versus-actual graph and its human interpretation
- [x] T093 [US6] [FR-023] Replace the flat fulfillment timeline with the selected order subgraph and simultaneous agent understanding
- [x] T094 [US6] [FR-023] Verify graph semantics, responsive fallback, Site contracts, build, policy, and final diff
- [x] T095 [US6] [FR-024] Add failing bilingual contracts for the concise financial plan-versus-actual graph
- [x] T096 [US6] [FR-024] Expand the existing Finance example with refund Evidence, Commitment, Ledger, Settlement, missing Payment, and safe agent action
- [x] T097 [US6] [FR-024] Verify Finance semantics, responsive fallback, Site contracts, build, policy, and final diff
- [x] T098 [US6] [FR-025] Specify and plan the education navigation label and selective-intake architecture explanation
- [x] T099 [US6] [FR-025] Add failing bilingual contracts for How it works navigation, lossless SourceRecords, and the small typed Reality vocabulary
- [x] T100 [US2] [FR-026] Add a failing Product Web boundary contract for the configured public-Site return link on unauthenticated account surfaces
- [x] T101 [US2] [FR-026] Configure `SITE_URL` for Product Web builds and make the auth brand return to the public Site
- [x] T102 [US2] [FR-026] Run Product Web contracts, translation audit, production build, Spec policy, and final diff review
- [x] T100 [US6] [FR-025] Implement and verify the responsive architecture explanation, shared navigation, Site contracts, build, policy, and final diff
- [x] T101 [US5] [FR-016] Update the approved package scope to one early-access Reality Core with Cloud and self-hosted operation
- [x] T102 [US5] [FR-016] Add failing contracts for one offer, build-time EUR price, configured admission capacity, immediate-access/waitlist semantics, and self-hosted download
- [x] T103 [US5] [FR-016] Implement and verify the single-offer platform page, public build configuration, responsive design, Site contracts, build, policy, and final diff

## Dependencies

### ERP Lite increment (2026-09-12)

- [x] T106 [US4] [FR-028] Add placement, capabilities, source semantics and future-dashboard assertions; update superseded mapping and numbering expectations in `provider-site/scripts/site-contract.test.mjs` and observe failure.
- [x] T107 [US4] [FR-028] Add the responsive section and corrected source copy in `provider-site/src/LandingPage.tsx`, `provider-site/src/landing.css`, and all catalogs in `provider-site/src/localization.tsx`; update `docs/WEB_SPEC.md`.
- [x] T108 [US4] [FR-028] Run Site format/tests/audit/build, spec policy and desktop/mobile visual review; record evidence and final review in `specs/022-public-site/quickstart.md`.

Sequence: T106 → T107 → T108. FR-028 scenarios 1–3 use contract assertions;
scenario 4 uses the all-language audit and rendered desktop/mobile review.

- [x] T109 [US4] [FR-028] Update the source-section assertion in `provider-site/scripts/site-contract.test.mjs`, remove the owner-selected readiness paragraph/link from `provider-site/src/LandingPage.tsx`, and verify Site gates and spec policy.

- [x] T104 [US2] [FR-027] Add a failing single-signup hero contract in `provider-site/scripts/site-contract.test.mjs`, retaining configured origin and language assertions.
- [x] T105 [US2] [FR-027] Simplify `provider-site/src/LandingPage.tsx`, reconcile Spec 095 discovery wording, verify Site tests/audits/build and rendered hero, and record evidence in `quickstart.md`.

```text
Specification/design gates
  -> failing proof
  -> US1 public Site
  -> US2 dedicated Product Web
  -> US3 CI/Compose/docs
  -> cross-cutting verification
```

US1 and US2 are released together because moving the landing page leaves one owner at
every point. US3 makes the split operable and is required in the same PR.

## Parallel Opportunities

- T004–T007 cover independent browser/repository contracts before extraction.
- T011 can proceed alongside Site workspace setup after target paths exist.
- T026–T027 update independent documentation/template families.
- T031–T033 are independent final static, policy, and backend regression gates.

## Implementation Strategy

The smallest coherent release includes both P1 stories: Site owns public presentation
and Web owns all account/product routes. The P2 story is required before merge because
unwired deployables are not operationally complete.

## Requirement Coverage

- [x] T115 [US4] [FR-028] Style the existing attribute list in `provider-site/src/LandingPage.tsx` and `provider-site/src/landing.css` as a responsive icon strip, verify Site gates, and update PR #209.

- [x] T114 [US4] [FR-028] Shorten the three ERP-section paragraphs in `provider-site/src/LandingPage.tsx` and `provider-site/src/localization.tsx`, update the existing contract, and verify Site gates before PR creation.

- [x] T113 [US4] [FR-028] Update graph contracts in `provider-site/scripts/site-contract.test.mjs`, reorder and clarify sections in `provider-site/src/LandingPage.tsx`, translate in `provider-site/src/localization.tsx`, improve diagram contrast/type in `provider-site/src/landing.css`, and verify Site gates and spec policy.

- [x] T112 [US4] [FR-028] Update `provider-site/scripts/site-contract.test.mjs` first, clarify the Context Graph foundation in `provider-site/src/LandingPage.tsx` and `provider-site/src/localization.tsx`, and verify Site gates and spec policy.

- [x] T111 [US4] [FR-028] Remove the dashboard teaser from `provider-site/src/LandingPage.tsx`, `provider-site/src/localization.tsx` and `provider-site/src/landing.css`; update `provider-site/scripts/site-contract.test.mjs` first and verify Site gates and spec policy.

- [x] T110 [US4] [FR-028] Update the ERP-section contract in `provider-site/scripts/site-contract.test.mjs`, implement ERP-optional and Build on Reality copy in `provider-site/src/LandingPage.tsx` and `provider-site/src/localization.tsx`, then verify Site gates and spec policy.

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-003 | T004, T008, T015, T030–T031 | T009–T014 | Complete |
| FR-004–FR-008 | T004–T007, T019–T020, T031 | T010–T13, T016–T018 | Complete |
| FR-009–FR-011 | T006, T029–T030, T032 | T021–T024, T028 | Complete |
| FR-012 | T006, T031–T032 | T014, T025–T28 | Complete |
| FR-013–FR-014 | T039, T043 | T040–T042 | Complete |
| DR-001–DR-003 | T007, T015, T020, T033–T034 | T010–T13, T016–T18 | Complete |
| FR-015 | T044, T046 | T045 | Complete |
| FR-016 | T050, T053 | T051–T052 | Complete |
