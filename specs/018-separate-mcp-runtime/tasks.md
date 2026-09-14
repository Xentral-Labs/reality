---
description: "Requirement-traceable HTTP-only separate MCP runtime tasks"
---

# Tasks: Separate MCP Runtime

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and
`quickstart.md`
**Gate**: Specification and plan approved, Constitution Check passed, and no unresolved
`[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede the implementation they prove.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner approval, HTTP-only scope, and closed clarification markers in `specs/018-separate-mcp-runtime/spec.md` and `specs/018-separate-mcp-runtime/checklists/requirements.md`
- [x] T002 Confirm all pre- and post-design Constitution Check rows remain PASS in `specs/018-separate-mcp-runtime/plan.md`
- [x] T003 Run `$speckit-analyze` for `specs/018-separate-mcp-runtime/` and resolve every CRITICAL or HIGH inconsistency across `spec.md`, `plan.md`, and `tasks.md`

## Phase 2: Foundational Tool and Configuration Contracts

**Goal**: Establish failing proof and the shared contracts every user story needs.

- [x] T004 [P] [FR-005] [FR-006] Add failing canonical registry uniqueness, schema, access-mode, and binding parity tests in `backend/tests/test_ai_mcp.py`
- [x] T005 [P] [FR-001] [FR-002] [FR-016] Add failing public-URL, listener-separation, production-HTTPS, endpoint-path, and bounded database-pool configuration tests in `backend/tests/test_mcp_http_runtime.py`
- [x] T006 [P] [DR-002] [DR-004] [DR-005] Add failing architecture assertions for one registry, shared proposal records, and non-authoritative URLs/labels in `backend/tests/test_ai_mcp.py`
- [x] T007 [FR-005] [FR-006] [DR-004] Consolidate tool metadata, structured inputs, access modes, and application bindings into one registry in `backend/src/reality/mcp/catalog.py`
- [x] T008 [FR-005] [FR-006] Adapt HTTP registration, allowlist validation, settings metadata, and direct dispatch to the canonical registry in `backend/src/reality/mcp/server.py` and `backend/src/reality/mcp/catalog.py`
- [x] T009 [FR-001] [FR-002] Implement shared validated MCP public URL and listener configuration in `backend/src/reality/mcp/config.py` and use it from `backend/src/reality/web/api.py`
- [x] T010 [FR-016] Implement generic validated database pool size, overflow, and timeout configuration in `backend/src/reality/db/core.py`

**Checkpoint**: Registry/configuration tests fail only on user-story runtime behavior; no
duplicate exposed-tool definition remains.

## Phase 3: User Story 1 — Dedicated HTTP Endpoint (P1)

**Goal**: An administrator can configure a client against a separate authenticated MCP
HTTP process while local development uses the same transport.

**Independent Test**: Start Web/API and MCP independently, create a restricted token
through settings, initialize an HTTP MCP client at the displayed URL, and execute one
allowed read while Web/API does not serve that protocol request.

- [x] T011 [P] [US1] [FR-001] [FR-003] Add failing dedicated ASGI initialize/list/call and independent-lifespan tests in `backend/tests/test_mcp_http_runtime.py`
- [x] T012 [P] [US1] [FR-002] [FR-018] Add failing exact `MCP_URL` settings response tests, including no `API_URL` fallback, in `backend/tests/test_master_data_api.py`
- [x] T013 [P] [US1] [FR-004] Add failing assertion that Web/API does not construct, start, or serve MCP in `backend/tests/test_http_boundary.py`
- [x] T014 [P] [US1] [FR-019] Add failing local authenticated HTTP-only client story in `backend/tests/test_mcp_http_runtime.py`
- [x] T015 [US1] [FR-001] [FR-003] Implement the dedicated MCP ASGI application and SDK session-manager lifespan in `backend/src/reality/mcp/app.py`
- [x] T016 [US1] [FR-001] [FR-018] Wire the exact public URL and narrow host/origin security into the authenticated server in `backend/src/reality/mcp/server.py`
- [x] T017 [US1] [FR-004] Remove MCP construction, lifespan ownership, and `/mcp` mount from `backend/src/reality/web/app.py`
- [x] T018 [US1] [FR-002] [FR-018] Return the independently configured MCP endpoint from company settings in `backend/src/reality/web/api.py`
- [x] T019 [US1] [FR-003] [FR-019] Add an independent `mcp` service, port, environment, migration dependency, and health wiring in `compose.yml` and `.env.example`
- [x] T020 [US1] [FR-019] Remove the frontend `/mcp/` proxy to Web/API in `frontend/nginx.conf`
- [x] T021 [US1] [FR-001] [FR-003] Run the US1 HTTP connection story and record verified commands/outcomes in `specs/018-separate-mcp-runtime/quickstart.md`

## Phase 4: User Story 2 — Tenant and Mutation Safety (P1)

**Goal**: Process separation preserves current tokens, tenant isolation, allowlists,
proposal-only mutation, and separately authorized execution.

**Independent Test**: Exercise valid, missing, malformed, revoked, wrong-tool, and
cross-tenant cases against the dedicated endpoint, then prove a mutation tool creates
only a proposal until separate confirmation.

- [x] T022 [P] [US2] [FR-007] [FR-008] [FR-010] Add failing authenticated HTTP token-subject, malformed/revoked token, and immediate-revocation tests in `backend/tests/test_mcp_http_runtime.py`
- [x] T023 [P] [US2] [FR-009] Add failing per-call allowlist reduction and forbidden-tool tests in `backend/tests/test_mcp_http_runtime.py`
- [x] T024 [P] [US2] [DR-003] [DR-005] Add failing cross-tenant opaque-ID non-disclosure and tenant-argument rejection tests in `backend/tests/test_mcp_http_runtime.py`
- [x] T025 [P] [US2] [FR-011] [FR-012] [FR-020] Add failing proposal-only, separate-confirmation, disconnect, and reconciliation business stories in `backend/tests/test_mcp_http_runtime.py`
- [x] T026 [US2] [FR-007] [FR-008] [FR-010] Preserve current database-backed token verification and make authenticated subject the only tenant source in `backend/src/reality/mcp/auth.py` and `backend/src/reality/mcp/server.py`
- [x] T027 [US2] [FR-009] Enforce the canonical registry allowlist on every protected HTTP tool call in `backend/src/reality/mcp/server.py`
- [x] T028 [US2] [FR-011] [FR-012] Route read, propose, and confirm modes through shared application handlers without direct adapter writes in `backend/src/reality/mcp/catalog.py` and `backend/src/reality/tools/application.py`
- [x] T029 [US2] [FR-020] Preserve durable proposal IDs and bounded error results needed for disconnect reconciliation in `backend/src/reality/mcp/catalog.py`
- [x] T030 [US2] [DR-001] [DR-002] [DR-003] Verify Source/Evidence/Reality traces, shared proposal authority, and tenant scope in representative HTTP MCP results in `backend/tests/test_mcp_http_runtime.py`

## Phase 5: User Story 3 — Independent Operation and Diagnosis (P2)

**Goal**: Operators can distinguish liveness/readiness, restart MCP independently, and
bound its share of shared PostgreSQL resources.

**Independent Test**: Keep Web/API healthy while restarting MCP; make the database or
registry unavailable and observe MCP liveness remain up while readiness returns a safe
503 and later recovers.

- [x] T031 [P] [US3] [FR-013] [FR-014] Add failing liveness/readiness success, dependency failure, recovery, and non-disclosure tests in `backend/tests/test_mcp_http_runtime.py`
- [x] T032 [P] [US3] [FR-015] Add failing Web/API-survives-MCP-restart topology smoke test in `backend/tests/test_mcp_http_runtime.py`
- [x] T033 [P] [US3] [FR-016] Add failing runtime-specific pool bounds and bounded pool-acquisition timeout tests in `backend/tests/test_postgresql_integration.py`
- [x] T034 [US3] [FR-013] [FR-014] Implement public liveness and bounded database/verifier/registry readiness routes in `backend/src/reality/mcp/app.py`
- [x] T035 [US3] [FR-015] Give MCP its own process command, listener, health check, and graceful lifecycle in `compose.yml` and `backend/Dockerfile`
- [x] T036 [US3] [FR-016] Configure separate backend and MCP pool budgets and document their aggregate connection ceiling in `compose.yml`, `.env.example`, and `specs/018-separate-mcp-runtime/contracts/runtime-configuration.md`
- [x] T037 [US3] [FR-013] [FR-015] Run the failure-isolation and recovery story and record evidence in `specs/018-separate-mcp-runtime/quickstart.md`

## Phase 6: User Story 4 — Controlled Migration Without Drift (P2)

**Goal**: Prove parity, remove every old transport path, and leave exactly one stable
HTTP MCP owner.

**Independent Test**: Compare the complete catalog and representative results/security
against the prior behavior, route the configured URL to the dedicated runtime, and
prove Web/API and repository surfaces contain no supported stdio or mounted MCP path.

- [x] T038 [P] [US4] [FR-006] [FR-017] Add full catalog name/schema/access/result parity and cutover-blocking tests in `backend/tests/test_mcp_http_runtime.py`
- [x] T039 [P] [US4] [FR-018] Add proxy-host mismatch, stable URL, and final-route ownership tests in `backend/tests/test_mcp_http_runtime.py` and `backend/tests/test_master_data_api.py`
- [x] T040 [P] [US4] [FR-023] Add repository policy test rejecting supported stdio imports, CLI/module entry points, and current documentation promises in `backend/tests/test_spec_policy.py`
- [x] T041 [P] [US4] [FR-024] Add failing Copilot registry-schema, direct-dispatch, tenant-scope, proposal-safety, and no-subprocess tests in `backend/tests/test_ai_mcp.py`
- [x] T042 [US4] [FR-023] Remove the `reality mcp` command and fixed-tenant transport options from `backend/src/reality/cli/app.py` and `backend/src/reality/mcp/server.py`
- [x] T043 [US4] [FR-023] Remove all stdio client imports, subprocess construction, and obsolete transport parameters from `backend/src/reality/agent/mcp_chat.py` and `backend/config/command_catalog.yaml`
- [x] T044 [US4] [FR-024] Refactor the internal Copilot model-tool loop to canonical in-process schema and dispatch in `backend/src/reality/agent/mcp_chat.py` and `backend/src/reality/services/core.py`
- [x] T045 [US4] [FR-017] [FR-018] Complete route cutover and rollback configuration with one MCP owner in `compose.yml`, `.env.example`, and `frontend/nginx.conf`
- [x] T046 [US4] [FR-017] Execute the parity/cutover suite and record the approved migration and rollback evidence in `specs/018-separate-mcp-runtime/quickstart.md`

## Phase 7: User Story 5 — Understand the Topology (P3)

**Goal**: Contributors and operators can identify all runtime, storage, URL, and shared
application responsibilities without reading source code.

**Independent Test**: A reviewer uses repository documentation to identify each
deployable runtime, both storage responsibilities, the shared application path, exact
public URLs, and the now-implemented HTTP-only MCP topology.

- [x] T047 [P] [US5] [FR-021] [FR-022] Add a documentation review checklist for current-state topology and HTTP-only wording in `specs/018-separate-mcp-runtime/checklists/documentation.md`
- [x] T048 [P] [US5] [DR-004] [DR-006] Add documentation assertions for shared-service direction and non-business OperationContext semantics in `backend/tests/test_spec_policy.py`
- [x] T049 [US5] [FR-021] [FR-022] Change the README target-state wording to implemented topology and document startup/URLs in `README.md`
- [x] T050 [US5] [FR-021] [FR-023] Update the remote HTTP-only product and CLI contracts in `docs/WEB_SPEC.md` and `docs/CLI_SPEC.md`
- [x] T051 [US5] [FR-021] [DR-004] Update runtime boundaries and supersede mounted routing in `docs/ARCHITECTURE.md` and `docs/decisions/0005-frontend-backend-object-storage.md`
- [x] T052 [US5] [FR-021] Run the independent documentation review and record approval in `specs/018-separate-mcp-runtime/checklists/documentation.md`

## Final Phase: Cross-Cutting Review

- [x] T053 [P] [FR-001] [FR-019] Run dedicated HTTP MCP tests in `backend/tests/test_mcp_http_runtime.py`
- [x] T054 [P] [FR-005] [FR-024] Run canonical registry, Copilot, token, and proposal tests in `backend/tests/test_ai_mcp.py`
- [x] T055 [P] [FR-002] [FR-021] Run frontend tests/build and verify Agents & AI renders the exact MCP endpoint through `frontend/src/App.tsx`
- [x] T056 [FR-003] [FR-013] [FR-015] Run the complete Compose smoke flow from `specs/018-separate-mcp-runtime/quickstart.md`
- [x] T057 [DR-001] [DR-002] [DR-003] Run the complete PostgreSQL suite under `backend/tests/` and reconcile tenant, proposal, and trace assertions against `specs/018-separate-mcp-runtime/spec.md`
- [x] T058 [FR-023] Run Ruff over `backend/src/` and `backend/tests/`, Spec Policy through `scripts/check_spec_policy.py`, and repository stdio/current-doc scans with no unsupported path remaining
- [x] T059 Confirm no Alembic/schema change was introduced against `specs/018-separate-mcp-runtime/data-model.md` and review rollback evidence in `specs/018-separate-mcp-runtime/plan.md`
- [x] T060 Review the final diff against every FR/DR row in `specs/018-separate-mcp-runtime/spec.md` and mark tasks/checklists complete only after all required checks are green

## Dependencies

```text
Specification/design gates
  -> foundational registry + configuration
  -> US1 dedicated endpoint
       -> US2 security parity
       -> US3 independent operations
  -> US4 migration/removal (requires US1-US3)
  -> US5 final current-state documentation (requires US4)
  -> cross-cutting verification
```

- US1 depends on the foundational registry and configuration contracts.
- US2 and US3 can proceed in parallel after the dedicated runtime skeleton exists.
- US4 depends on US1-US3 because old paths cannot be removed before parity, security,
  readiness, and rollback evidence exist.
- US5 finalizes current-state wording only after cutover behavior is complete.

## Parallel Execution Examples

- Foundational: T004, T005, and T006 touch separate test concerns and can run in
  parallel before T007-T010.
- US1: T011-T014 can be written in parallel; T015-T020 then follow their failing proof.
- US2: T022-T025 are parallel security/business-story tests before T026-T030.
- US3: T031-T033 can be written in parallel before T034-T036.
- US4: T038-T041 cover parity, routing, policy, and Copilot independently before removal
  tasks T042-T045.
- US5: T047-T048 can precede documentation changes; architecture and product docs may
  be updated in parallel once US4 is green.

## Implementation Strategy

### MVP

Complete Phase 1, Phase 2, and US1 to prove a dedicated authenticated HTTP endpoint and
independent lifecycle while retaining the old route only inside controlled parity
tests. This is demonstrable but not a completed production cutover.

### Safe cutover

Complete US2 and US3 before US4. Do not remove the mounted/stdin paths until security,
proposal behavior, readiness, stable URL, and rollback evidence pass. Complete US5 and
the final phase in the same release that declares HTTP-only topology implemented.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-004 | T005, T011–T014 | T009, T015–T021 | Complete |
| FR-005–FR-006 | T004, T038 | T007–T008 | Complete |
| FR-007–FR-010 | T022–T024 | T026–T027 | Complete |
| FR-011–FR-012 | T025, T030 | T028–T029 | Complete |
| FR-013–FR-016 | T031–T033 | T034–T037 | Complete |
| FR-017–FR-018 | T038–T039 | T045–T046 | Complete |
| FR-019–FR-020 | T014, T025 | T019, T029 | Complete |
| FR-021–FR-022 | T047–T048, T055 | T049–T052 | Complete |
| FR-023–FR-024 | T040–T041 | T042–T044, T050 | Complete |
| DR-001–DR-003 | T024, T030, T057 | T026, T028–T030 | Complete |
| DR-004–DR-006 | T006, T048 | T007–T008, T044, T051 | Complete |
