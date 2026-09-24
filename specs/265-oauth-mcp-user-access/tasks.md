---
description: "Requirement-traceable OAuth MCP user authorization implementation tasks"
---

# Tasks: OAuth MCP User Access

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and
`quickstart.md`
**Gate**: Product/domain and architecture scope approved on 2026-09-24; Constitution
Check passed; no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede the implementation they prove where practical. Do
not mark a task complete while its required proof is red.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [X] T001 Record the owner-approved specification and architecture review state in `specs/265-oauth-mcp-user-access/spec.md` and `specs/265-oauth-mcp-user-access/plan.md`
- [ ] T002 Complete the reviewer-owned authorization requirements review in `specs/265-oauth-mcp-user-access/checklists/security.md`; resolve every finding in the source spec/plan/contracts before marking it approved
- [ ] T003 Run `$speckit-analyze` against `specs/265-oauth-mcp-user-access/`, resolve every CRITICAL cross-artifact finding, re-run `make spec-check`, and record the green artifact gate in `specs/265-oauth-mcp-user-access/quickstart.md`
- [X] T004 [FR-001] [FR-021] [FR-022] Prove the installed MCP SDK can serve the `2026-07-28` stateless resource-server contract with a separate issuer, add a focused executable compatibility probe, and pin or upgrade the supported version in `packages/reality-core/pyproject.toml` before authorization implementation

## Phase 2: Foundational Security Authority

**Goal**: Establish the additive account/security model, principal contract and
test-first state-machine boundary shared by every user story.

- [X] T005 [P] [FR-004] [FR-010] [FR-011] Add failing grant, interaction, PKCE/code, hashed credential, expiry, rotation, replay and revocation service tests in `packages/reality-core/tests/test_mcp_oauth_service.py`
- [X] T006 [P] [DR-002] [DR-004] [DR-005] Add failing schema, composite tenant-key, lifecycle constraint, empty downgrade and populated downgrade-refusal tests in `packages/reality-core/tests/test_mcp_oauth_migration.py`
- [X] T007 [P] [FR-018] [DR-001] [DR-003] Add failing principal isolation, server-owned tenant/actor context, no-business-schema-change and canonical-dispatch contract assertions in `packages/reality-core/tests/test_ai_mcp.py`
- [X] T008 [DR-002] [DR-004] [DR-005] Add `MCPClientGrant`, `MCPAuthorizationInteraction` and `MCPUserCredential` with the reviewed constraints in `packages/reality-core/src/reality/db/mcp_authorization.py` and register metadata in `packages/reality-core/src/reality/db/core.py`
- [X] T009 [DR-002] [DR-004] [DR-005] Create additive migration `packages/reality-core/migrations/versions/0094_mcp_user_authorization.py`, including downgrade refusal after data exists and no change to business tables or `mcp_access_token`
- [X] T010 [FR-018] [DR-003] Define immutable manual/interactive `MCPPrincipal` and internal actor propagation in `packages/reality-core/src/reality/mcp/principal.py` without adding user/tenant fields to public tool schemas
- [X] T011 [FR-004] [FR-010] [FR-011] Implement transaction-bound interaction, grant, code, credential, refresh rotation/reuse and revocation primitives in `packages/reality-core/src/reality/services/mcp_authorization.py`
- [X] T012 [FR-019] [DR-005] Add bounded redacted authorization lifecycle audit helpers using `SecurityAuditEvent` in `packages/reality-core/src/reality/services/mcp_authorization.py`; exclude state, codes, tokens, PKCE material and business payloads
- [X] T013 Run the new foundational tests and preserve their command/output evidence in `specs/265-oauth-mcp-user-access/quickstart.md`

## Phase 3: User Story 1 — Connect with a Reality account (P1)

**Goal**: A compatible client discovers Reality authorization, the user signs in,
selects one ready business company, approves exact read access and completes a read
without a manual token.

**Independent test**: Configure only the MCP URL in a clean compatible client, complete
PKCE sign-in/consent for one company and call one permitted read; cancellation and
invalid credentials yield no grant or disclosure.

- [X] T014 [P] [US1] [FR-001] [FR-002] [FR-003] [FR-021] Add failing protected-resource discovery, RFC 8414/OIDC metadata, 401 challenge, PKCE S256, issuer/resource/redirect/state and token-exchange HTTP contract tests in `packages/reality-core/tests/test_mcp_oauth_http.py`
- [X] T015 [P] [US1] [FR-004] [FR-005] [FR-006] [FR-008] [FR-020] Add failing interaction read/approve/deny, all-current-eligible-tools preselection with individual deselection, one-company selection, same-name company, cancellation, expiry and account-switch API tests in `packages/reality-core/tests/test_mcp_oauth_http.py`
- [X] T016 [P] [US1] [FR-022] Add failing pre-registered and CIMD client tests covering exact metadata/redirect matching, HTTPS-only fetch, DNS/IP rebinding, private/reserved targets, redirects, size and timeout bounds in `packages/reality-core/tests/test_mcp_oauth_http.py`
- [X] T017 [US1] [FR-001] [FR-002] [FR-021] Extend canonical resource/issuer validation in `packages/reality-core/src/reality/mcp/config.py` and publish RFC 9728 metadata plus correct 401/403 challenges from `packages/reality-core/src/reality/mcp/app.py` and `packages/reality-core/src/reality/mcp/server.py`
- [X] T018 [US1] [FR-001] [FR-003] [FR-021] Implement RFC 8414/OIDC discovery, Authorization Code + PKCE S256, RFC 9207 issuer, RFC 8707 resource-bound token exchange and RFC 7009 revocation adapters in `packages/reality-core/src/reality/web/mcp_authorization.py`; register only the required public routes in `packages/reality-core/src/reality/web/app.py`
- [X] T019 [US1] [FR-022] Implement bounded pre-registration configuration and SSRF-safe CIMD resolution in `packages/reality-core/src/reality/services/mcp_authorization.py`; do not add Dynamic Client Registration
- [X] T020 [US1] [FR-004] [FR-005] [FR-006] [FR-008] Implement session-authenticated interaction read/approve/deny APIs from `contracts/web-api.md` in `packages/reality-core/src/reality/web/mcp_authorization.py` with all current coarse-scope-eligible tools initially selected, individual deselection and commit-time account/membership/company/client rechecks
- [X] T021 [US1] [FR-003] [FR-004] [FR-005] [FR-008] Add typed browser interaction methods and response models in `apps/web/src/api.ts` and implement the fixed `/oauth/authorize` consent route with all eligible tools selected and individually deselectable in `apps/web/src/OAuthAuthorization.tsx`
- [X] T022 [US1] [FR-003] [FR-020] Route signed-out/login return by opaque interaction ID only in `apps/web/src/Auth.tsx` and `apps/web/src/entryRouting.ts`; reject arbitrary redirect URIs and exclude OAuth secrets from browser persistence
- [X] T023 [US1] [FR-004] [FR-020] Add English/German/Dutch/Spanish consent, cancellation, expiry and failure copy in `apps/web/src/localization.tsx`
- [X] T024 [US1] Run the US1 independent API/MCP/browser journey and record evidence in `specs/265-oauth-mcp-user-access/quickstart.md`

## Phase 4: User Story 2 — Exercise only granted authority (P1)

**Goal**: Every call is constrained by the current user, client, one company, scopes,
exact tools and current service policy; consent never crosses the proposal/confirmation
boundary.

**Independent test**: Authorize two clients differently and exercise permitted,
ungranted, removed-membership, wrong-company, proposal and confirmation cases; only
the exact authorized effects occur.

- [X] T025 [P] [US2] [FR-007] [FR-008] [FR-009] [FR-010] Add failing effective-authority intersection tests for disabled users, removed memberships, archived/wrong tenants, wrong clients/resources, insufficient scopes, exact-tool denial and later catalog growth in `packages/reality-core/tests/test_mcp_oauth_service.py`
- [X] T026 [P] [US2] [FR-012] [FR-018] Add failing read/propose/confirm business stories proving consent has zero business effect, proposals remain pending and verified human identity is injected only server-side in `packages/reality-core/tests/test_ai_mcp.py`
- [X] T027 [P] [US2] [DR-001] [DR-003] Add failing cross-tenant not-found and unchanged Source → Evidence → Reality trace assertions for interactive/manual parity in `packages/reality-core/tests/test_mcp_oauth_service.py`
- [X] T028 [US2] [FR-007] [FR-008] [FR-009] [FR-010] Implement live account, membership, tenant-purpose/archive, grant, client, resource, scope and exact-tool resolution in `packages/reality-core/src/reality/services/mcp_authorization.py`
- [X] T029 [US2] [FR-007] [FR-010] [FR-018] Compose manual and interactive verification without changing manual-token semantics in `packages/reality-core/src/reality/mcp/auth.py`
- [X] T030 [US2] [FR-008] [FR-009] [FR-018] Make MCP dispatch consume only `MCPPrincipal`, enforce current access class/tool intersection and forward tenant/actor internally in `packages/reality-core/src/reality/mcp/server.py` and `packages/reality-core/src/reality/mcp/catalog.py`
- [X] T031 [US2] [FR-012] Preserve proposal-first and separate explicit confirmation behavior while attaching verified actor context in `packages/reality-core/src/reality/mcp/catalog.py` and the existing shared confirmation service paths it invokes
- [X] T032 [US2] Run the US2 independent authority/proposal/tenant story and record evidence in `specs/265-oauth-mcp-user-access/quickstart.md`

## Phase 5: User Story 3 — Create a first company during connection (P1)

**Goal**: An eligible user without a company can separately confirm canonical
company setup, recover it idempotently, wait for readiness and resume the same consent.

**Independent test**: Create and recover an ordinary company and a Sandbox from consent,
prove one owner membership/setup identity for each, and bind each exact ready company;
cancellation, ineligibility and failure create no usable external grant.

- [X] T033 [P] [US3] [FR-013] [FR-014] Add failing consent-to-company-setup parity, separate confirmation, duplicate/lost-response recovery, readiness and exact-tenant resume API tests in `packages/reality-core/tests/test_company_setup_api.py`
- [X] T034 [P] [US3] [FR-013] [FR-014] [FR-017] [FR-020] Add failing browser journeys for cancel, ordinary and Sandbox company creation, initializing/failed recovery, ineligible account and both ready company types receiving equivalent interactive/manual MCP eligibility in `apps/web/scripts/mcp-oauth-browser.mjs`
- [X] T035 [US3] [FR-013] [FR-014] Reuse `company_setup.options`, `create_company`, `read_request` and `retry_request` without parallel writes, adding only a narrowly scoped interaction-resume result if proven necessary in `packages/reality-core/src/reality/web/mcp_authorization.py`
- [X] T036 [US3] [FR-013] [FR-014] Wrap the existing company setup form/progress components for return to the same opaque consent interaction in `apps/web/src/OAuthAuthorization.tsx` and `apps/web/src/unified/setupProgress.ts`
- [X] T037 [US3] [FR-014] [FR-017] [FR-020] Enforce ready-company eligibility for ordinary and Sandbox companies with identical MCP authority rules in `packages/reality-core/src/reality/services/mcp_authorization.py`, manual-token creation and `apps/web/src/OAuthAuthorization.tsx`
- [X] T038 [US3] Run the US3 independent create/recover/resume journey and record evidence in `specs/265-oauth-mcp-user-access/quickstart.md`

## Phase 6: User Story 4 — Inspect and revoke connected clients (P2)

**Goal**: Users and company owners can inspect attributable interactive grants and
revoke one without exposing secrets or changing unrelated grants/manual tokens.

**Independent test**: Create two interactive grants and one manual token, inspect both
authorized views, revoke one grant and prove immediate isolated denial.

- [X] T039 [P] [US4] [FR-015] [FR-016] [FR-019] Add failing personal/company-owner inventory, same-company re-consent supersession, distinct-company grant, cross-tenant not-found, revocation and redaction service/API tests in `packages/reality-core/tests/test_mcp_oauth_service.py` and `packages/reality-core/tests/test_mcp_oauth_http.py`
- [X] T040 [P] [US4] [FR-015] [FR-019] Add failing personal/company grant-management browser states, confirmation, unknown response, reload and no-secret DOM/storage assertions in `apps/web/scripts/mcp-oauth-browser.mjs`
- [X] T041 [US4] [FR-015] [FR-016] [FR-019] Implement shared user/company grant inventory, effective-state explanation, immutable re-consent and idempotent revoke services in `packages/reality-core/src/reality/services/mcp_authorization.py`
- [X] T042 [US4] [FR-015] [FR-019] Expose personal and company-owner grant endpoints from `contracts/web-api.md` in `packages/reality-core/src/reality/web/mcp_authorization.py` with exact ownership and tenant checks
- [X] T043 [US4] [FR-015] [FR-017] Present separate Connected clients and Manual API tokens sections in `apps/web/src/unified/MCPAccess.tsx` and add the personal/company entries in `apps/web/src/unified/SettingsPage.tsx`
- [X] T044 [US4] [FR-015] [FR-019] Add four-language grant inventory, effective-state, revoke confirmation and recovery copy in `apps/web/src/localization.tsx`
- [X] T045 [US4] Run the US4 independent inspect/revoke/isolation journey and record evidence in `specs/265-oauth-mcp-user-access/quickstart.md`

## Phase 7: User Story 5 — Preserve unattended integrations and interoperability (P2)

**Goal**: Existing manual tokens remain stable while two independent current clients
use standard interactive discovery and both credential kinds reach the same tools.

**Independent test**: Execute equivalent reads through both credential kinds, deny an
unsupported client safely, exercise authorization outage behavior and complete/revoke
two independent supported client connections.

- [X] T046 [P] [US5] [FR-017] [FR-018] Extend manual-token, wildcard/exact-tool, revocation, Playground refusal and interactive/manual parity regression tests in `packages/reality-core/tests/test_ai_mcp.py` and `packages/reality-core/tests/test_mcp_http_runtime.py`
- [X] T047 [P] [US5] [FR-020] [FR-021] [FR-022] Add authorization-service outage, unsupported client, issuer change, metadata-cache invalidation and no-insecure-fallback tests in `packages/reality-core/tests/test_mcp_oauth_http.py`
- [X] T048 [US5] [FR-017] [FR-018] Preserve `MCPAccessToken` creation/list/revoke and verifier behavior while exposing distinct credential-kind attribution in `packages/reality-core/src/reality/mcp/auth.py` and `packages/reality-core/src/reality/web/api.py`
- [X] T049 [US5] [FR-020] [FR-021] [FR-022] Finalize strict compatibility failure and outage responses in `packages/reality-core/src/reality/web/mcp_authorization.py` and `packages/reality-core/src/reality/mcp/app.py` without anonymous/shared downgrade
- [X] T050 [US5] [FR-017] [FR-019] Update manual/interactive management labels and security-safe operational telemetry in `apps/web/src/unified/MCPAccess.tsx` and `packages/reality-core/src/reality/telemetry.py`
- [ ] T051 [US5] Validate the full connect/read/elevate/revoke sequence with two independent current MCP clients and record exact versions/results in `specs/265-oauth-mcp-user-access/quickstart.md`

## Final Phase: Documentation, Retention and Cross-Cutting Review

- [ ] T052 [P] [FR-019] [DR-005] Implement and test the interaction-creation retention sweep capped at 500 terminal interactions older than 7 days and 500 terminal credentials older than 90 days in `packages/reality-core/src/reality/services/mcp_authorization.py` and `packages/reality-core/tests/test_mcp_oauth_service.py`; do not add a timer, scheduler or public cleanup endpoint
- [ ] T053 [P] [FR-001] [FR-017] [FR-021] Document the durable user authorization, discovery, manual-token coexistence, Sandbox boundary and operator configuration contract in `docs/features/mcp-user-authorization.md`, `docs/WEB_SPEC.md` and `docs/ARCHITECTURE.md`
- [ ] T054 [P] [DR-001] [DR-002] [DR-004] [DR-005] Reconcile the account/security entities, non-business authority and unchanged Source → Evidence → Reality boundary in `docs/DATA_MODEL.md` and `docs/TEST_STRATEGY.md`
- [ ] T055 [FR-001–FR-022] [DR-001–DR-005] Run `make spec-check` and audit every requirement row in this file against its test and implementation/documentation tasks
- [ ] T056 Run Ruff and the complete PostgreSQL backend suite required by `docs/TEST_STRATEGY.md`; record exact pass/skip evidence in `specs/265-oauth-mcp-user-access/quickstart.md`
- [ ] T057 Run frontend format/build, four-language i18n audit and all applicable browser/layout/accessibility journeys; record evidence in `specs/265-oauth-mcp-user-access/quickstart.md`
- [ ] T058 Review migration `0094_mcp_user_authorization.py` through empty up/down/up, populated downgrade refusal, tenant-key catalog and rollback procedure; record evidence in `specs/265-oauth-mcp-user-access/quickstart.md`
- [ ] T059 Run `make docs-generate` and `make docs-catalog-check` if any command, tool, view, projection, exception, event or MCP input schema changed; otherwise record the concrete no-impact reason in `specs/265-oauth-mcp-user-access/quickstart.md`
- [ ] T060 Review the final diff against the Constitution, `spec.md`, both contracts, reviewer-owned `checklists/security.md` and shortest true links; create `specs/265-oauth-mcp-user-access/review.md` with findings and resolution
- [ ] T061 Update `docs/V0_CHECKLIST.md` and feature status only after T055–T060 and every required acceptance proof are green

## Dependencies

```text
Phase 1 gates
    ↓
Phase 2 foundational security authority
    ↓
US1 discovery/login/consent
    ↓
US2 effective authority and proposal boundary
    ├───────────────┐
    ↓               ↓
US3 company setup   US4 grant management
    └───────┬───────┘
            ↓
US5 compatibility/interoperability
            ↓
Final documentation and release gates
```

- US1 depends on the foundational state model and can be demonstrated with an existing
  ready business company.
- US2 depends on US1 credentials/principal and completes the security-critical P1 MVP.
- US3 depends on US1 interaction resume but is independently testable with a no-company
  account.
- US4 depends on grants from US1 but may proceed in parallel with US3 after US2's
  effective-authority semantics are stable.
- US5 depends on US1/US2 and consumes the management distinction from US4; its two-client
  evidence is a release gate, not a prerequisite for earlier local stories.

## Parallel Execution Examples

- Foundational: T005, T006 and T007 can be written in parallel before T008–T012.
- US1: T014–T016 can be written in parallel; after backend contracts stabilize, T021–T023
  can proceed alongside T017–T020 in separate files.
- US2: T025–T027 are independent failing proofs before T028–T031.
- US3 and US4 may proceed in parallel after US2, with T033/T034 and T039/T040 split
  between backend and browser evidence.
- US5: T046 and T047 can proceed in parallel before T048–T050.
- Final documentation T053/T054 and retention T052 can proceed in parallel after feature
  behavior stabilizes; release gates T055–T061 remain ordered.

## Implementation Strategy

### Security-first MVP

The smallest deployable interactive slice is Phase 1 + Phase 2 + US1 + US2. It connects
an existing eligible user/company, enforces one-company exact-tool authority and retains
the proposal/confirmation boundary. It is not advertised publicly until US4 management,
US5 two-client compatibility and all final release gates pass.

### Incremental delivery

1. Land inactive additive persistence and tested authorization state transitions.
2. Add discovery, PKCE and consent behind a disabled deployment setting.
3. Prove effective tenant/tool/user authority and business confirmation isolation.
4. Add canonical company setup resume and connected-client management.
5. Prove existing manual-token compatibility and two independent clients.
6. Reconcile durable docs, run complete gates, review, then enable deliberately.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-003 | T014 | T017–T018, T021–T023, T053 | Pending |
| FR-004–FR-006 | T005, T015 | T011, T020–T021 | Pending |
| FR-007–FR-010 | T025 | T028–T030 | Pending |
| FR-011 | T005 | T011 | Pending |
| FR-012 | T026 | T031 | Pending |
| FR-013–FR-014 | T033–T034 | T035–T037 | Pending |
| FR-015–FR-016 | T039–T040 | T041–T044 | Pending |
| FR-017–FR-018 | T007, T026–T027, T046 | T010, T029–T031, T043, T048, T053 | Pending |
| FR-019 | T039–T040, T052 | T012, T041–T044, T050, T052 | Pending |
| FR-020 | T015, T034, T047 | T022–T023, T037, T049 | Pending |
| FR-021–FR-022 | T014, T016, T047 | T017–T019, T049, T053 | Pending |
| DR-001 | T007, T027 | T030–T031, T054 | Pending |
| DR-002 | T006 | T008–T009, T054 | Pending |
| DR-003 | T007, T027 | T010, T028–T031 | Pending |
| DR-004 | T006 | T008–T009, T035, T054 | Pending |
| DR-005 | T006, T052 | T008–T009, T012, T052, T054 | Pending |
