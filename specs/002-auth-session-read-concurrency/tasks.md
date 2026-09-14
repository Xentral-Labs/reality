# Tasks: Non-Blocking Authenticated Reads

## Phase 1: Specification and Analysis

- [x] T001 [FR-001–FR-005] Approve `spec.md` with no unresolved clarification
- [x] T002 [FR-001–FR-005] Pass the Constitution Check in `plan.md`
- [x] T003 [FR-001–FR-005] Analyze spec, plan, and task consistency

## Phase 2: Regression Proof and Implementation

- [x] T004 [US1] [FR-002] [FR-005] Add a failing SQL-observation regression test in `backend/tests/test_user_access.py`
- [x] T005 [US1] [FR-001] [FR-002] Remove the read-path session mutation in `backend/src/reality/web/auth.py`
- [x] T006 [US1] [FR-003] [FR-004] Run the complete user-access test module from `backend/tests/test_user_access.py`

## Phase 3: Verification and Recovery

- [x] T007 [SC-002] Run spec policy, lint, full backend tests, frontend build, and translation audit
- [x] T008 [SC-003] Restart the local backend and frontend services
- [x] T009 [SC-003] Verify health, PostgreSQL activity, and browser bootstrap responsiveness
- [x] T010 Review the final diff against this spec and the Constitution
