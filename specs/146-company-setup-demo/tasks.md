# Tasks: Company Setup and Continuous Demo Data

Status: all 44 implementation and local acceptance tasks verified on 2026-09-09. Evidence is recorded in quickstart.md and review.md; no live deployment or merge. Reviewer-owned requirements checklist markers are unchanged.

## Phase 1: Review gate and foundation

- [x] T001 Record explicit approval of the two tables, supporting FK uniqueness, narrow Sandbox authorities and queued cancellation in `specs/146-company-setup-demo/review.md`; recheck Constitution PASS before migrations/runtime changes.
- [x] T002 [FR-006] [FR-014] [FR-017] [DR-001] Add failing roundtrip, same-tenant FK, owner/request uniqueness and cross-environment collision tests in `packages/reality-core/tests/test_company_setup_migration.py`.
- [x] T003 [FR-006] [FR-014] [FR-017] [DR-001] Add reviewed receipt/connection models in `packages/reality-core/src/reality/db/company_setup.py` and `demo_data.py`, metadata registration/supporting SourceSystem uniqueness in `db/core.py`, and next unused migration in `packages/reality-core/migrations/versions/`.
- [x] T004 [FR-006] [FR-009] [FR-018] [DR-001] Add failing caller-owned commit/rollback tests in `packages/reality-core/tests/test_demo_data_intake.py`, covering existing external callers and interpreter error paths.
- [x] T005 [FR-006] [FR-009] [FR-018] [DR-001] Extract transaction-bound source/interpretation and seed-required shared helpers in `packages/reality-core/src/reality/services/core.py`; preserve existing public default commit/error contracts and reject silent commit suppression.
- [x] T006 [FR-005] [FR-009] [FR-020] [DR-001] [DR-004] Add failing narrowly scoped profile-seed/intake policy tests in `packages/reality-core/tests/test_demo_data_security.py`; include pending owner, foreign tenant, ordinary company, archived/execution run, unready profile and revoked membership.
- [x] T007 [FR-005] [FR-009] [FR-020] [DR-001] [DR-004] Implement session/transaction/run-bound profile and incoming-order authorities in `packages/reality-core/src/reality/services/tenant_policy.py`; never broaden general Sandbox or production admission.

## Phase 2: US1 / US2 — One clear creation journey (P1)

- [x] T008 [US1] [FR-001] [FR-002] [FR-005] [FR-006] Add failing account options, request recovery, exact destination and invitation/membership precedence tests in `packages/reality-core/tests/test_company_setup_api.py`.
- [x] T009 [US2] [FR-003] [FR-004] [FR-006] [FR-007] [DR-001] Add failing empty/content/environment matrix, owner-level concurrency, cross-kind changed replay, cancellation and zero-synthetic-record tests in `packages/reality-core/tests/test_company_setup.py`.
- [x] T010 [US2] [FR-003] [FR-004] [FR-006] [FR-007] Implement shared creation/options/status/retry orchestration in `packages/reality-core/src/reality/services/company_setup.py`; ordinary atomic receipt and new empty practice preset reuse existing Playground lifecycle in `services/playground.py`.
- [x] T011 [US1] [FR-001] [FR-002] [FR-005] [FR-006] Add `packages/reality-core/src/reality/web/company_setup_api.py` and mount only reviewed paths in `web/app.py`; legacy `web/api.py` company creation delegates with required request key and canonical demo-Sandbox mapping.
- [x] T012 [US1] [FR-001] [FR-002] [FR-013] Add failing first/later form, prefill, application-copy and request persistence contracts in `apps/web/scripts/company-setup-contract.test.mjs`; update old onboarding assertions while retaining compact-lesson coverage.
- [x] T013 [US2] [FR-003] [FR-004] [FR-006] [FR-007] [FR-013] Add shared `apps/web/src/components/CompanySetupForm.tsx` and `CompanySetup.tsx`, typed `api.ts` contracts, all three later-entry replacements and initial entry in `App.tsx`; preserve explicit active-company routing and prior company state.
- [x] T014 [US1] [FR-001] [FR-002] [FR-005] [FR-013] Update `apps/web/src/Auth.tsx`, existing Playground entry and localization sources for access-request meaning, pending direct cockpit destination and truthful empty Sandbox labels.

## Phase 3: US3 — Canonical operational business (P1)

- [x] T015 [US3] [FR-008] [FR-009] [FR-011] [DR-001] [DR-002] Add failing count, ten-case, location/unit/procurement, correction/release and source-lineage stories in `packages/reality-core/tests/scenarios/test_international_demo.py`.
- [x] T016 [US3] [FR-008] [FR-011] [DR-003] Add pure versioned catalog/payload/manifest validation in `packages/reality-core/src/reality/demo/international.py` and `profile_contract.py`; preserve actual source-stated values and stable international vocabulary.
- [x] T017 [US3] [FR-008] [FR-009] [FR-011] [DR-001] [DR-002] Implement bounded atomic baseline preparation through shared services in `packages/reality-core/src/reality/services/demo_profile.py` and new preset dispatch in `services/playground.py`; never fabricate an executed proposal or silently modify old lesson presets.
- [x] T018 [US3] [FR-006] [FR-008] [FR-011] Add replay/version mismatch/partial rollback/manifest cap and first-versus-later equivalence tests in `packages/reality-core/tests/test_company_setup.py` and `tests/scenarios/test_international_demo.py` before enabling ready state.
- [x] T019 [US3] [FR-008] [FR-011] [FR-013] Expose ready profile/case/capability links and failed/in-progress states through `packages/reality-core/src/reality/web/company_setup_api.py` and `apps/web/src/components/CompanySetup.tsx`; no partial profile is labelled ready.

## Phase 4: US4 — Comparable history and separate execution (P2)

- [x] T020 [US4] [FR-010] [FR-011] [DR-003] Add failing twelve-week/two-window, cohort, linked credit/return, outlier, zero-baseline, EUR/USD and audit-time proofs in `packages/reality-core/tests/test_demo_profile_history.py`.
- [x] T021 [US4] [FR-010] [FR-011] [DR-003] Extend `packages/reality-core/src/reality/demo/international.py` and `services/demo_profile.py` with authored historical sources and postings; mark unsupported costs/promotions/price authority absent and retain gross-booked metric wording.
- [x] T022 [US4] [FR-012] [DR-001] [DR-004] Add failing unexecuted one-unit success/refusal, actual preview-confirmation/receipt, same-request replay and fresh-tenant repeat tests in `packages/reality-core/tests/test_demo_execution_profile.py`.
- [x] T023 [US4] [FR-012] [DR-004] Implement execution-profile provisioning in `packages/reality-core/src/reality/services/demo_profile.py` and explicit confirmation adapter/UI in `web/company_setup_api.py` and `apps/web/src/components/CompanySetup.tsx`; retain original analysis/execution evidence and disallow continuous source there.

## Phase 5: US5 — Optional ongoing Demo Data integration (P1)

- [x] T024 [US5] [FR-014] [FR-015] [FR-017] [FR-020] Add failing stopped-by-default, exact prerequisite preview, populated incompatibility, lifecycle/request revision and source authority tests in `packages/reality-core/tests/test_demo_data.py`.
- [x] T025 [US5] [FR-017] [DR-004] Add failing queued-only cancellation/history, current revision, active-claim and unknown-outcome tests in `packages/reality-core/tests/test_scheduled_job_recovery.py`; preserve ordinary pause semantics.
- [x] T026 [US5] [FR-017] [DR-004] Implement reviewed queued cancellation in `packages/reality-core/src/reality/services/scheduled_jobs.py`; update `specs/147-scheduled-jobs/spec.md` and `contracts/worker.md` to distinguish the extension from its prior runtime.
- [x] T027 [US5] [FR-014] [FR-015] [FR-017] [FR-020] Implement connection, explicit master-prerequisite creation, start/pause/resume/rate/stop/disconnect/reconnect in `packages/reality-core/src/reality/services/demo_data.py`; reuse schedules as continuous-run identities and enforce documented lock order.
- [x] T028 [US5] [FR-016] [FR-018] [FR-019] [FR-020] [DR-001] [DR-002] [DR-003] [DR-004] Add failing ten-interval real worker/import, duplicate delivery, closed browser, baseline isolation, backpressure20 and transaction-failure stories in `packages/reality-core/tests/test_demo_data_intake.py`.
- [x] T029 [US5] [FR-018] [DR-001] [DR-002] [DR-003] Add deterministic synthetic payload producer/interpreter in `packages/reality-core/src/reality/integrations/demo_data.py` and normal registry binding in `services/core.py`; preserve lossless source identity and call shared evidence/commitment helpers only.
- [x] T030 [US5] [FR-016] [FR-018] [FR-019] [FR-020] Register `demo.generate_orders` in `packages/reality-core/src/reality/jobs/handlers/demo_data.py` and `jobs/registry.py`; enforce current source/owner eligibility, bounded backlog and caller-owned transaction without direct network/business actions.
- [x] T031 [US5] [FR-014] [FR-019] [FR-020] Add failing App/owned-Playground adapter, pending isolation, counts/cursor/link and error redaction tests in `packages/reality-core/tests/test_demo_data_api.py`.
- [x] T032 [US5] [FR-014] [FR-017] [FR-019] [FR-020] Add shared status/pagination in `services/demo_data.py`, thin `packages/reality-core/src/reality/web/demo_data_api.py`, exact route mounts, and `config/connector_catalog.yaml` synthetic integration entry; no generic Chat mutation.
- [x] T033 [US5] [FR-013] [FR-014] [FR-015] [FR-017] [FR-019] Add failing integration discovery/control/confirmation/status and localization contracts in `apps/web/scripts/demo-data-contract.test.mjs` before UI implementation.
- [x] T034 [US5] [FR-013] [FR-014] [FR-015] [FR-017] [FR-019] Implement `apps/web/src/components/DemoDataIntegration.tsx`, typed `api.ts`, normal `App.tsx` Integrations and owned Playground presentation; setup shortcut configures only and never implicitly starts arrivals.

## Final phase: Discovery, verification and review

- [x] T035 [FR-001] [FR-013] [FR-014] [DR-001] Reconcile `docs/features/company-setup-demo.md`, `docs/WEB_SPEC.md`, `docs/DEMO_SPEC.md`, architecture/data-model/test/CLI contracts, `AGENTS.md`, `README.md` and spec 027 demo-entrypoint documentation; distinguish compact lesson, canonical baseline and optional live source.
- [x] T036 [FR-005] [FR-020] [DR-001] Register new boundaries and actual test evidence in `packages/reality-core/config/tenant_isolation_catalog.yaml`, `src/reality/catalogs.py` and `docs/SPEC_COVERAGE_MATRIX.md`; retain complete catalog drift tests.
- [x] T037 [FR-013] Run real browser acceptance at mobile/desktop in four languages/light/dark, keyboard validation, request-loss recovery and source controls; record evidence in `specs/146-company-setup-demo/quickstart.md`.
- [x] T038 Run final `make lint`, full PostgreSQL `make test`, migration/constraint proofs and scheduler/worker container acceptance; record actual results in `specs/146-company-setup-demo/quickstart.md`, including existing import/lesson/spec 147 regressions.
- [x] T039 Run `make spec-check`, `make site-build`, `make web-build`, `make docs-build` and i18n audits; re-run Spec Kit requirement/link analysis and record no-critical findings in `specs/146-company-setup-demo/review.md`.
- [x] T040 Review all 24 FR/DR and nine success criteria, then mark only green evidence complete in `specs/146-company-setup-demo/tasks.md` and `docs/V0_CHECKLIST.md`; no automatic deployment or merge.

## Dependencies and delivery

T001 blocks migration/runtime changes. Foundation T002–007 precedes services. US1/US2 require foundation; operational US3 precedes ready demo release. US4 extends the baseline and execution proof; US5 relies on shared catalog/prerequisites and spec 147, and may be implemented before historical US4 internally. Release as a complete canonical demo requires both history and operational proofs, not a partial seed labelled ready. T025 precedes T026; T028 precedes producer/handler; UI contract tests precede UI changes.

Independent work after the gate may cover pure catalog tests, creation UI contract tests and source tests in separate paths. Shared core/authorization edits remain coordinated. This task map does not authorize bypassing the gate or parallel changes to the same files.

## Requirement coverage

| Requirement | Test tasks | Implementation/docs |
|---|---|---|
| FR-001 | T008, T012 | T011, T014, T035 |
| FR-002 | T008, T012 | T010, T011, T013, T014 |
| FR-003 | T009, T012 | T010, T013 |
| FR-004 | T009 | T010, T013 |
| FR-005 | T006, T008 | T007, T011, T014, T036 |
| FR-006 | T002, T004, T008, T009, T018 | T003, T005, T010, T011, T013 |
| FR-007 | T009 | T010, T013 |
| FR-008 | T015, T018 | T016, T017, T019 |
| FR-009 | T004, T006, T015 | T005, T007, T017 |
| FR-010 | T020 | T021 |
| FR-011 | T015, T018, T020 | T016, T017, T019, T021 |
| FR-012 | T022 | T023 |
| FR-013 | T012, T033, T037 | T013, T014, T019, T034, T035 |
| FR-014 | T002, T024, T031, T033 | T003, T027, T032, T034 |
| FR-015 | T024, T033 | T027, T034 |
| FR-016 | T028 | T030 |
| FR-017 | T002, T024, T025, T033 | T003, T026, T027, T032, T034 |
| FR-018 | T004, T028 | T005, T029, T030 |
| FR-019 | T028, T031, T033 | T030, T032, T034 |
| FR-020 | T006, T024, T028, T031 | T007, T027, T030, T032, T036 |
| DR-001 | T002, T004, T006, T009, T015, T022, T028 | T003, T005, T007, T017, T029, T036 |
| DR-002 | T015, T028 | T017, T029 |
| DR-003 | T020, T028 | T016, T021, T029 |
| DR-004 | T006, T022, T025, T028 | T007, T023, T026, T029 |

SC-001/002/004 → T008–014/018; SC-003 → T015–021; SC-005 → T022/023; SC-006 → T035–040; SC-007/008/009 → T024–034. All implementation tasks are backed by the local verification evidence in quickstart.md.

## Live-creation refinement (FR-021, owner-approved 2026-09-09)

- [x] T041 Add failing service and API proofs for automatically connected/running live setup, rejected combinations, rollback/recovery and replay after pause in `packages/reality-core/tests/test_company_setup.py` and `packages/reality-core/tests/test_company_setup_api.py`.
- [x] T042 Implement durable live intent and atomic orchestration in `packages/reality-core/src/reality/services/company_setup.py`, `playground.py` and `demo_data.py`; extend `web/company_setup_api.py`.
- [x] T043 Add shared form choice in `apps/web/src/components/CompanySetupForm.tsx`, four-language copy in `localization.tsx`, persisted `api.ts` request and browser/contract proof in `apps/web/scripts/company-setup-browser.mjs` and `company-setup-contract.test.mjs`.
- [x] T044 Reconcile durable setup/integration contracts and verify full backend, frontend, browser, lint and spec gates; record results and review.

## Port 8080 integration

- [x] T045 Port shared setup/demo/scheduler services into the current unified-app checkout, preserving its domain changes and tenant catalog.
- [x] T046 Add the reviewed migration-branch join and rehearse against a restored local database backup.
- [x] T047 Replace unified CompanySettings creation with the shared form and add Demo Data to unified DataSourcesPage; preserve current inspectors and routes.
- [x] T048 Verify service regressions, full backend and frontend gates, and actual 8080 creation choices.
- [x] T049 Build matching local API, web, scheduler and worker; migrate once, update the local stack and record observed health/asset evidence.

- [x] T050 [FR-022] Add scoped company presentation metadata and API proof; group unified company cards and show environment/demo/live state with four-language labels; verify browser layout and complete regression gates.

FR-022 → T050; unified-app/local-stack integration → T045–049. Final evidence is in quickstart.md and docs/LOCAL_STACK.md.

- [x] T051 [FR-023] Update browser acceptance for one three-choice group, defaults, selection transitions and demo-only live intent.
- [x] T052 [FR-023] Implement the shared goal-based form and four-language copy.
- [x] T053 [FR-023] Verify web contracts/build/i18n, browser matrix, spec/docs and local 8080 web rollout; record review.

- [x] T054 [FR-024] Add missing-name browser regression; implement localized required/helper/error feedback, focus and retained choices; verify web/browser/spec gates and update local web.

- [x] T055 [FR-025] Update browser acceptance and implement automatic ready entry, recovery/error retry and destination confirmation; verify frontend/browser/spec/docs and local web rollout.

## Sandbox clarity and live activity refinement

- [x] T056 [FR-026–028] Add Sandbox Reports and recent-import ordering regressions.
- [x] T057 [FR-026–028] Implement scoped reads, compact badge and localized demo controls/live widget.
- [x] T058 [FR-026–028] Verify backend/frontend/browser/spec/docs and local rollout.

- [x] T059 [FR-029] Move Demo Data to its own Company navigation destination; verify route, conditional menu, isolated integration view, mobile/localized layout and local web deployment.

- [x] T060 [FR-030] Reproduce Sandbox Exceptions failure, replace the two inappropriate read guards, verify focused/full/backend and real local demo reads, and update local matching core images.

## FR-031
- [x] T031 Refine setup states, typography and status indicators without changing creation semantics.
- [x] T032 Verify delayed setup, same-request retry and responsive localized rendering.

## FR-032

- [x] T932 Add card-entry and unsupported-company browser regressions.
- [x] T933 Reuse simulation controls and confirmed demo setup with localized fallback.
- [x] T934 Verify build, contracts, browser coverage, language and spec checks; create PR.

- [x] T935 Polish the unavailable simulation card and replace inline creation with Companies navigation; verify heading/padding, desktop/mobile snapshots, read-only handoff and local gates.
- [ ] T936 Verify the PR pipeline before merge/deployment.

- [x] T937 Explain the unsupported Sandbox data setup; verify localized copy and existing navigation.

- [x] T938 Group and format connection preview; verify exact references, disclosure access, responsive layout and confirmation boundary.

- [x] T939 [FR-006/021] Reproduce deferred seed/live-start interruption, make incomplete setup a retryable worker failure with transaction rollback, and verify explicit recovery reuses the same tenant without partial evidence or connection state.
- [x] T940 [FR-031] Expose bounded automatic setup-retry progress, show the current/completed/remaining steps and next attempt in the shared localized setup screen, then verify frontend, PostgreSQL and visible port-8080 behavior.
- [x] T941 [FR-031] Simplify setup to one progress hierarchy, route exhausted recovery through the confirmed retry endpoint, remove stale ready-state failure metadata, and give the isolated worker enough bounded connections for the canonical DB1/DB2 generation.
- [x] T942 [FR-033] Add failing setup and browser-progress regressions for a four-step checklist and a ready initial Finance projection; rebuild shared materialized projections inside confirmed demo initialization, preserve atomic retry, then verify a fresh port-8080 company without manual Finance refresh.
- [x] T943 [FR-034] Make queued work visibly active and hold the truthful completed four-step state before automatic navigation; verify timing and a fresh visible setup.
- [x] T944 [FR-035] Enforce dated, uniformly numbered demo invoices and complete retained DB values for every demo sales-invoice line, including continuous live intake; verify a fresh port-8080 company.
