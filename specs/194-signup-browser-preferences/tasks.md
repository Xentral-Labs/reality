# Tasks: Signup Adopts the Browser's Presentation Defaults

## Phase 1: Specification and Design Gates

- [x] T001 Record scope, requirements and non-goals in `spec.md`.
- [x] T002 Pass the Constitution Check and resolve the design in `plan.md`.
- [x] T003 Analyze `spec.md`, `plan.md` and `tasks.md` for coverage before implementation.

## Phase 2: User Stories 1-3 — Account creation adopts the hint

- [x] T004 [US1] [US2] [FR-001] [FR-003] Add failing signup and invitation-signup tests for stored zone, language and paired locale in `packages/reality-core/tests/test_user_access.py`.
- [x] T005 [US3] [FR-002] [DR-002] Add failing fallback tests for absent, empty, unknown, malformed and unsupported hints in `packages/reality-core/tests/test_user_access.py`.
- [x] T006 [US1] [US2] [US3] [FR-001] [FR-002] [FR-003] [DR-001] [DR-002] Implement `SUPPORTED_LOCALES`, `presentation_defaults()` and the optional request fields in `packages/reality-core/src/reality/web/auth.py`, reusing them in `validate_preferences()`.

## Phase 3: User Stories 1-2 — The browser states what it knows

- [x] T007 [US1] [US2] [FR-004] Add failing browser resolution tests in `apps/web/scripts/signup-preferences.test.mjs`.
- [x] T008 [US1] [US2] [FR-004] Implement `apps/web/src/signupPreferences.ts` and send the hint from `apps/web/src/api.ts` and `apps/web/src/Auth.tsx`.

## Final Phase: Verification and Review

- [x] T009 [FR-005] Run the backend access suite, web contract tests, lint, spec and build gates; record results in `quickstart.md`.
- [x] T010 Review every FR/DR against the diff, confirm no schema change and record rollback in `review.md`.
