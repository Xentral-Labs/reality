---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: MCP Permission Ceiling Follows the Catalog

**Input**: `spec.md`, `plan.md` and `research.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes and resulting repository artifacts MUST be written in
English. Paths are relative to the repository root; `core/` abbreviates `packages/reality-core/`.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

`[P]` marks tasks that touch different files and may run in parallel. Every functional requirement
appears in at least one test task and one implementation task. Test tasks precede the code they
prove and are observed failing first. Every negative test carries a positive control.

## Phase 1: Specification and Design Gates

- [ ] T001 Confirm owner approval of scope in `specs/269-mcp-permission-ceiling/spec.md`, and that
  deleting the ceiling rather than raising it is the accepted reading of FR-001
- [X] T002 Correct the specification: the consent screen shows `Reality API returned 422`, not the
  generic "Authorization could not be completed" the Context section claimed (research R4); the
  unhandled `ValueError` behind an unknown tool name is now stated in Context; the catalog count and
  the headroom moved from 179/21 to 180/20 after spec 270 merged
- [ ] T003 Confirm every Constitution Check row is PASS and that no schema or migration is
  introduced, in `specs/269-mcp-permission-ceiling/plan.md`
- [ ] T004 Run the analysis pass across `specs/269-mcp-permission-ceiling/` and resolve every
  CRITICAL or HIGH finding

## Phase 2: User Story 1 — Connecting survives catalog growth (P1)

**Independent test**: approval with every eligible tool selected succeeds, counted from the catalog.

### Tests

- [ ] T005 [P] [US1] [FR-001] [FR-006] [FR-007] Add a failing HTTP test that approves an
  authorization with every tool the requested scopes make eligible, for each combination of
  supported scopes, taking the expected count from `MCP_TOOL_NAMES` rather than writing it, in
  `core/tests/test_mcp_oauth_http.py`
- [ ] T006 [US1] Observe T005 failing for the right reason before the change: temporarily lower the
  bound below the catalog size, confirm the refusal, and restore it. Record the observation in
  `tasks.md` rather than only asserting it happened
- [ ] T007 [P] [US1] [FR-002] Add a failing test that a list repeating a name and using one of the
  four legacy aliases is accepted and stored once. Positive control: the de-duplicated equivalent
  produces the same grant, in `core/tests/test_mcp_oauth_service.py`
- [ ] T008 [P] [US1] [FR-001] Add a test that a wildcard is still refused for an interactive grant,
  so deleting the length bound cannot be read as relaxing what a grant may contain. Positive
  control: the explicit equivalent list is accepted, in `core/tests/test_mcp_oauth_service.py`

### Implementation

- [ ] T009 [US1] [FR-001] [FR-002] Remove `max_length` from `Approval.allowed_tools` in
  `core/src/reality/web/mcp_authorization.py`, keeping `min_length=1`, so the bound is the
  membership rule in `validate_tool_permissions` and nothing else

## Phase 3: User Story 2 — A refused list says what is wrong (P2)

**Independent test**: an unknown tool name answers 400 naming the tool, not 500.

### Tests

- [ ] T010 [P] [US2] [FR-004] Add a failing HTTP test that approving with an unknown tool name
  answers 400 and names the tool in the body, where it answers 500 today (research R3). Positive
  control: a valid list in the same test is accepted, in `core/tests/test_mcp_oauth_http.py`
- [ ] T011 [P] [US2] [FR-004] Add a failing HTTP test that an empty permission list stays refused
  with a stated reason, and that tools outside the requested scopes keep their existing sentence, in
  `core/tests/test_mcp_oauth_http.py`
- [ ] T012 [P] [US2] [FR-005] Add a test that every refusal of this endpoint carries `detail` as a
  string, which is the shape `apps/web/src/api.ts` surfaces; a refusal whose `detail` is a list
  cannot reach the owner. Positive control: assert the accepted case returns no `detail`, in
  `core/tests/test_mcp_oauth_http.py`
- [ ] T013 [P] [US2] [FR-005] Add a test that a refused approval leaves the interaction `pending`,
  so the owner can correct the selection instead of restarting the client, in
  `core/tests/test_mcp_oauth_http.py`

### Implementation

- [ ] T014 [US2] [FR-004] [FR-005] Add a `ValueError` arm to `approve()` in
  `core/src/reality/web/mcp_authorization.py` answering 400 with `str(error)`, matching what
  `post_mcp_token` already answers for the same exception

## Phase 4: User Story 3 — Both grant paths accept the same permissions (P3)

### Tests

- [ ] T015 [US3] [FR-003] Add `core/tests/test_mcp_permission_parity.py`: the same four lists — the
  complete catalog, a duplicate-laden list, an unknown name, an empty list — submitted to
  interactive approval and to manual token creation produce the same acceptance and the same
  message. Positive control: both accept the complete catalog
- [ ] T016 [US3] [FR-003] Add the new test file to `docs/SPEC_COVERAGE_MATRIX.md` under this spec's
  section

## Phase 5: Verification

- [ ] T017 Run the focused suite: `pytest core/tests/test_mcp_oauth_http.py
  core/tests/test_mcp_oauth_service.py core/tests/test_mcp_permission_parity.py`
- [ ] T018 Run the catalog and gate suite: `pytest core/tests/test_application_catalog.py
  core/tests/test_tool_catalog.py core/tests/tenant_isolation`
- [ ] T019 Run `ruff check . --no-cache` and `ruff format` from `packages/reality-core`
- [ ] T020 Run the complete backend suite and record the evidence in
  `specs/269-mcp-permission-ceiling/checklists/requirements.md`. Spec 270 showed that a second copy
  of a literal can keep the focused suites green while the full run is red, so this is not optional
- [ ] T021 Search the repository for any other permission-length literal before calling the feature
  done, so the ceiling cannot survive in a layer this plan did not read

## Requirement Coverage

| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T005, T006, T008 | T009 |
| FR-002 | T007 | T009 |
| FR-003 | T015 | T014, T016 |
| FR-004 | T010, T011, T015 | T014 |
| FR-005 | T012, T013 | T014 |
| FR-006 | T005 | T009 |
| FR-007 | T005, T006 | T005 as the standing regression proof |

## Dependencies

Phase 1 precedes everything; T002 corrects the specification before anything is built against its
wrong sentence. Phases 2 and 3 are independent: the ceiling and the unhandled `ValueError` are
separate defects in the same handler, and either can ship alone. Phase 4 depends on both, since it
compares what they produce. Phase 5 depends on all of them.
