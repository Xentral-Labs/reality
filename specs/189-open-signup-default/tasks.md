# Tasks: Open Signup by Default

## Phase 1: Specification and Design Gates

- [x] T001 Record authorized scope and reviewed requirements in `spec.md` and `checklists/requirements.md`.
- [x] T002 Pass Constitution Check and resolve design in `plan.md`.
- [x] T003 Analyze `spec.md`, `plan.md` and `tasks.md` before implementation.

## Phase 2: User Stories 1 and 2 — Admission

- [x] T004 [US1] [FR-001] [FR-003] [FR-005] Add failing default/blank HTTP admission and replay tests in `packages/reality-core/tests/test_user_access.py`.
- [x] T005 [US2] [FR-002] [FR-003] [DR-001] Add policy matrix, atomic counter and mode-transition tests in `packages/reality-core/tests/test_access_admission.py`.
- [x] T006 [US1] [FR-001] [FR-003] [FR-005] [DR-001] Implement shared policy in `packages/reality-core/src/reality/services/access_admission.py` and reuse in `web/auth.py`, preserving guards.
- [x] T007 [US2] [FR-002] [DR-001] Preserve finite/manual behavior in shared policy and document account/tenant boundaries in `docs/WEB_SPEC.md`.

## Phase 3: User Story 3 — Presentation and Defaults

- [x] T008 [US3] [FR-004] Add optional-capacity and default-configuration proof in `packages/reality-core/tests/test_platform_admin_overview.py`, `test_access_admission.py` and `provider-site/scripts/site-contract.test.mjs`.
- [x] T009 [US3] [FR-004] Reuse admission policy in `services/platform.py`; update `apps/web/src/Auth.tsx`, `api.ts`, `localization.tsx` and `provider-site/src/PlatformPage.tsx`, `localization.tsx`.
- [x] T010 [US3] [FR-004] Align generic defaults in `.env.example`, Compose, installer, Helm values and Site build; document explicit Railway overrides and installation semantics in `docs/RAILWAY_DEMO.md` and `apps/docs/content/`.

## Final Phase: Verification and Review

- [x] T011 Run full backend, lint, spec, frontend and documentation gates; record results in `quickstart.md`.
- [x] T012 Review all FR/DR, nullable API compatibility, no schema diff and rollback in `review.md`; mark completion only with green evidence.

## Dependencies and Strategy

T001–T003 precede tests. T004–T005 precede T006–T007. T008 precedes T009–T010.
T011–T012 follow all implementation. US1+US2 form the minimum coherent policy change;
US3 completes the prospect/operator contract. Independent backend and frontend
checks can run concurrently; implementation remains sequential in this checkout.

## Requirement Coverage

| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T004 | T006 |
| FR-002 | T005 | T007 |
| FR-003 | T004–T005 | T006 |
| FR-004 | T008 | T009–T010 |
| FR-005 | T004, T011 | T006–T007 |
| DR-001 | T005, T012 | T006–T007 |
