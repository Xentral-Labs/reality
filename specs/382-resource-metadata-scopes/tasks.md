---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Resource Metadata Lists Every Supported Scope

**Input**: `spec.md` and `plan.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

`core/` abbreviates `packages/reality-core/`.

## Phase 1: Gates

- [ ] T001 Owner approval of scope and of the decision that `reality:read` stays required
- [X] T002 Constitution Check all PASS, no schema change

## Phase 2: Tests first

- [X] T003 [US1] [FR-001] Resource metadata lists all supported scopes, equal to the
  authorization server's, and an unauthenticated call answers 401, in
  `core/tests/test_mcp_http_runtime.py`
- [X] T004 [US2] [FR-002] [FR-003] A one-proposal-tool grant holds `reality:read`, its token
  states it, and its principal permits only that tool, in
  `core/tests/test_mcp_oauth_service.py`
- [X] T005 Observe T003 and T004 failing on `origin/main` — `['reality:read']` published;
  grant scopes `['reality:propose']`

## Phase 3: Implementation

- [X] T006 [FR-001] Replace the protected-resource metadata route in
  `core/src/reality/mcp/server.py`
- [X] T007 [FR-002] Add `REQUIRED_SCOPE` to every approved grant in
  `core/src/reality/services/mcp_authorization.py`
- [X] T008 Add this spec's tests to `docs/SPEC_COVERAGE_MATRIX.md`

## Phase 4: Verification

- [X] T009 `pytest core/tests/test_mcp_http_runtime.py core/tests/test_mcp_oauth_service.py
  core/tests/test_mcp_oauth_http.py core/tests/test_mcp_permission_parity.py
  core/tests/test_ai_mcp.py`
- [X] T010 `ruff check` and `ruff format --check` on touched files; `make spec-check`
- [ ] T011 Complete backend suite in CI

## Requirement Coverage

| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T003 | T006 |
| FR-002 | T004 | T007 |
| FR-003 | T004, existing scope-narrowing test | T007 |
