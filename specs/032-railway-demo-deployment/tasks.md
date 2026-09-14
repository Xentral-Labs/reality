---
description: "Requirement-traceable tasks for the temporary Railway demo deployment"
---

# Tasks: Temporary Hosted Product Demo

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/hosted-demo-profile.md`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review and close clarification markers in `specs/032-railway-demo-deployment/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS in `specs/032-railway-demo-deployment/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve every CRITICAL finding in `specs/032-railway-demo-deployment/`

## Phase 2: Failing Proof

- [x] T004 [P] [US1] [FR-001,FR-002,FR-006] Add failing configurable private-upstream assertions in `apps/web/scripts/product-boundary.test.mjs`
- [x] T005 [P] [US1] [FR-004,FR-005,FR-007,FR-008] Add failing hosted-profile contract assertions in `packages/reality-core/tests/test_repository_layout.py`
- [x] T006 [P] [US1] [FR-012] Add failing public-signup-disabled authentication tests in `packages/reality-core/tests/test_user_access.py`
- [x] T007 [P] [US2] [FR-003,DR-001,DR-002,DR-003,DR-004] Identify and run existing PostgreSQL persistence, tenant, migration, and domain regression proofs listed in `specs/032-railway-demo-deployment/quickstart.md`
- [x] T008 [P] [US3] [FR-009,FR-010,FR-011] Add failing operator-guide setup and cleanup assertions in `packages/reality-core/tests/test_repository_layout.py`

## Phase 3: User Story 1 — Open a hosted Reality demo (P1)

- [x] T009 [US1] [FR-001,FR-002,FR-006] Replace the fixed Nginx configuration with a runtime-filtered `API_UPSTREAM` template in `apps/web/default.conf.template` and `apps/web/Dockerfile`
- [x] T010 [US1] [FR-004,FR-008] Document and automate the API migration gate and full-path health contract in `docs/RAILWAY_DEMO.md`
- [x] T011 [US1] [FR-005,FR-007,FR-012] Implement and document hosted signup disabling in `packages/reality-core/src/reality/web/auth.py` and `docs/RAILWAY_DEMO.md`
- [x] T012 [US1] [FR-001,FR-002,FR-004,FR-005,FR-006,FR-007,FR-008] Provision private PostgreSQL/API and public Product Web in the dedicated Railway project, then record non-secret resource identifiers and verification results in `specs/032-railway-demo-deployment/quickstart.md`
- [x] T013 [US1] Run the external HTTPS, unauthenticated access, secure-cookie, private-exposure, and synthetic-tenant acceptance checks from `specs/032-railway-demo-deployment/quickstart.md`
- [x] T019 [US1] [FR-002a] Add a failing runtime DNS re-resolution assertion to `apps/web/scripts/product-boundary.test.mjs`, configure the Nginx variable upstream and container resolver in `apps/web/default.conf.template`, and verify recovery after an API-only Railway redeploy

## Phase 4: User Story 2 — Restart without losing business records (P2)

- [ ] T014 [US2] [FR-003] Record a stable synthetic tenant/Reality identifier, restart the hosted API, re-read it, and append the redacted result to `specs/032-railway-demo-deployment/quickstart.md`
- [x] T015 [US2] [FR-004,FR-008] Verify the configured pre-deploy migration command and health gate from provider state/logs without exposing secrets, recording the result in `specs/032-railway-demo-deployment/quickstart.md`
- [x] T016 [US2] [DR-001,DR-002,DR-003,DR-004] Run existing domain, tenant-isolation, and migration regression suites from `packages/reality-core/tests/`

## Phase 5: User Story 3 — Remove the temporary environment safely (P3)

- [x] T017 [US3] [FR-009,FR-010,FR-011] Complete setup, logging, shutdown, ephemeral-artifact, billing, and destructive-cleanup instructions in `docs/RAILWAY_DEMO.md`
- [ ] T018 [US3] [FR-009] Rehearse non-destructive public-domain disablement steps or verify them against current provider state, then document the exact owner-confirmed destructive cleanup boundary in `docs/RAILWAY_DEMO.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `python3 scripts/check_spec_policy.py` and reconcile the requirement traceability table
- [ ] T901 Run Ruff and the complete backend PostgreSQL suite
- [x] T902 Run Product Web contract tests and production build
- [x] T903 Confirm no schema change and review migration/rollback behavior
- [x] T904 Review the final diff against the Constitution and all FR/DR requirements
- [ ] T905 Update task and verification status only after required checks are green

## Background deployment follow-up

- [x] T020 [US2] [FR-013] Add failing repository contracts for the allowlisted background image, deployment order and heartbeat gate.
- [x] T021 [US2] [FR-013] Add the Railway background image and deploy scheduler/worker after the API migration gate.
- [x] T022 [US2] [FR-013] Document one-time private variables, deployment, verification and rollback.
- [x] T023 [US2] [FR-013] Run focused deployment tests, spec policy, formatting and shell syntax checks; review the final diff.

## Dependencies

- T003 blocks implementation.
- T004–T008 are failing proofs and precede T009–T011 and T017.
- T009–T011 block hosted provisioning T012.
- T012 blocks external verification T013–T015.
- US2 depends on the US1 hosted environment; US3 documentation can proceed independently, while destructive cleanup occurs only after the demonstration and explicit owner confirmation.

## Parallel Opportunities

- T004, T005, T006, T007, and T008 touch independent proof areas and can run in parallel.
- T010, T011, and T017 edit the same guide and therefore execute sequentially despite covering independent requirements.
- Local regression suites in T016 can run while hosted service deployment converges after T012.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001, FR-002, FR-006 | T004, T013 | T009, T012 | Complete |
| FR-002a | T019 | T019 | Complete |
| FR-003 | T007, T014, T016 | T012 | Pending |
| FR-004, FR-008 | T005, T015 | T010, T012 | Complete |
| FR-005, FR-007, FR-012 | T005, T006, T013 | T011, T012 | Complete |
| FR-009, FR-010, FR-011 | T008, T018 | T010, T011, T017 | Pending |
| DR-001, DR-002, DR-003, DR-004 | T007, T016 | T009, T012 | Pending |

## Implementation Strategy

The MVP is US1: a secure hosted Product Web with private API/PostgreSQL and external smoke proof. US2 adds restart persistence evidence. US3 supplies cleanup safety now, while destructive removal remains deferred until the owner confirms the demonstration is over.
