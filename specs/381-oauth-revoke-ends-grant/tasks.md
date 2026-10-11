---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Revoking a Refresh Token Ends Its Grant

**Input**: `spec.md` and `plan.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

Paths are relative to the repository root; `core/` abbreviates `packages/reality-core/`.

## Phase 1: Gates

- [ ] T001 Owner approval of scope in `specs/381-oauth-revoke-ends-grant/spec.md`
- [X] T002 Confirm every Constitution Check row is PASS and no schema change, in `plan.md`

## Phase 2: Tests first

- [X] T003 [US1] [US2] [FR-001] [FR-003] [FR-004] Refresh revocation after one rotation ends
  the grant, refuses both access tokens and the refresh token, and is idempotent, in
  `core/tests/test_mcp_oauth_service.py`
- [X] T004 [US1] [FR-001] Revoking the rotated refresh token ends the grant, in
  `core/tests/test_mcp_oauth_service.py`
- [X] T005 [US2] [FR-002] Current access token ends the grant; rotated access token ends only
  itself and the grant renews (positive control), in `core/tests/test_mcp_oauth_service.py`
- [X] T006 [FR-004] Unknown token changes nothing, in `core/tests/test_mcp_oauth_service.py`
- [X] T007 [US1] [FR-001] [FR-003] [FR-004] HTTP revocation lists the client as revoked and
  refuses the refresh exchange, in `core/tests/test_mcp_oauth_http.py`
- [X] T008 Observe T003, T004, T005 (current access token) and T007 failing against
  `origin/main`'s service — 4 failed, the two positive controls passed

## Phase 3: Implementation

- [X] T009 [FR-001] [FR-002] [FR-003] Route refresh and current-access revocation into
  `revoke_grant(reason="client_revoked")`, and allow `actor_user_id=None`, in
  `core/src/reality/services/mcp_authorization.py`
- [X] T010 [FR-003] Label `client_revoked` in German, Dutch and Spanish in
  `apps/web/src/localization.tsx`
- [X] T011 Add this spec's tests to `docs/SPEC_COVERAGE_MATRIX.md`

## Phase 4: Verification

- [X] T012 Focused OAuth suites: `pytest core/tests/test_mcp_oauth_http.py
  core/tests/test_mcp_oauth_service.py core/tests/test_mcp_permission_parity.py
  core/tests/test_mcp_oauth_migration.py`
- [X] T013 `ruff check . --no-cache` and `ruff format --check .` from `core/`;
  `make spec-check`; `npm run i18n:audit` in `apps/web`
- [ ] T014 Complete backend suite in CI

## Requirement Coverage

| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T003, T004, T007 | T009 |
| FR-002 | T005 | T009 |
| FR-003 | T003, T007 | T009, T010 |
| FR-004 | T003, T006, T007 | unchanged adapter |
