# Tasks: Live Activity Signal

## Phase 1: Specification and Gates

- [x] T001 [FR-001-FR-007] Capture approved scope and acceptance scenarios in `specs/061-live-activity-signal/spec.md`
- [x] T002 [DR-001-DR-003] Pass the Constitution Check in `specs/061-live-activity-signal/plan.md`
- [x] T003 Analyze requirement/task coverage with no critical findings

## Phase 2: Failing Proof

- [x] T004 [FR-001-FR-003] Add failing activity-signal service/API and isolation-catalog tests in `packages/reality-core/tests/test_master_data_api.py`, `packages/reality-core/tests/test_business_events.py`, and `packages/reality-core/tests/test_application_catalog.py`
- [x] T005 [FR-003-FR-007] Add failing frontend live-activity contracts in `apps/web/scripts/workspace-actions-contract.test.mjs`

## Phase 3: Implementation

- [x] T006 [FR-001] [DR-001-DR-003] Implement the tenant-scoped aggregate signal service, isolation-catalog classification, and GET adapter in `packages/reality-core/src/reality/services/core.py`, `packages/reality-core/config/tenant_isolation_catalog.yaml`, and `packages/reality-core/src/reality/web/api.py`
- [x] T007 [FR-002-FR-007] Implement typed polling, unread navigation, Activity refresh, and localized attention notification in `apps/web/src/api.ts`, `apps/web/src/App.tsx`, `apps/web/src/localization.tsx`, and `apps/web/src/tailwind.css`

## Phase 4: Verification

- [x] T008 [SC-001-SC-004] Run focused tests, frontend format/build, spec check, and diff review
