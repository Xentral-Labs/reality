---
description: "Requirement-traceable Company Membership Invitations implementation tasks"
---

# Tasks: Company Membership Invitations

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/http-membership-api.md`, and `quickstart.md`
**Gate**: Constitution Check passed; specification and plan approved on 2026-09-02;
no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede the implementation they prove.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Record the 2026-09-02 specification and plan approvals and confirm zero clarification markers in `specs/035-company-membership-invitations/spec.md`, `plan.md`, and `checklists/requirements.md`
- [x] T002 Confirm and record the completed review of all 36 requirement-quality questions in `specs/035-company-membership-invitations/checklists/access-security.md`
- [x] T003 Re-run `make spec-check` and record the result in `specs/035-company-membership-invitations/checklists/requirements.md`
- [x] T004 Run `$speckit-analyze`, resolve every CRITICAL finding across `spec.md`, `plan.md`, and `tasks.md`, and record the result in `specs/035-company-membership-invitations/checklists/requirements.md`

## Phase 2: Foundational Persistence and Shared Boundaries

**Goal**: Establish the tested schema, constraints, catalogs, and service primitives
required by every user story.

- [x] T005 [P] [DR-002] [DR-003] Add failing model/catalog parity and shortest-link assertions for CompanyInvitation, InvitationDelivery, TenantMembership, and SecurityAuditEvent in `packages/reality-core/tests/test_data_model.py`
- [x] T006 [P] [FR-007] [FR-018] [FR-029] [DR-004] [DR-006] Add failing fresh-upgrade, `terminal_at` retention-anchor, existing-membership preservation, constraint, index, and guarded-downgrade tests in `packages/reality-core/tests/test_migrations.py`
- [x] T007 [P] [FR-021] [DR-005] Add failing invitation, delivery, audit, and membership operation classifications to the executable isolation coverage expectations in `packages/reality-core/tests/test_application_catalog.py` and `packages/reality-core/tests/tenant_isolation/test_families.py`
- [x] T008 [FR-007] [FR-018] [FR-029] [DR-002] [DR-003] [DR-004] Implement CompanyInvitation with `terminal_at`, InvitationDelivery, constrained TenantMembership, and extended SecurityAuditEvent in `packages/reality-core/src/reality/db/core.py`
- [x] T009 [FR-007] [FR-018] [FR-029] [DR-002] [DR-003] [DR-004] Add the guarded schema and `terminal_at` retention anchor in migration `packages/reality-core/migrations/versions/0030_company_membership_invitations.py`
- [x] T010 [P] [DR-001] [DR-002] [DR-003] Update access entities and administrative-Evidence classification in `packages/reality-core/config/data_model.yaml` and `docs/DATA_MODEL.md`
- [x] T011 [FR-021] [DR-005] Register all shared invitation, delivery, audit, and membership operations in `packages/reality-core/config/tenant_isolation_catalog.yaml`
- [x] T012 [FR-001] [FR-013] [FR-021] [FR-026] Implement explicit principal, owner/platform-admin guards, tenant lock order, normalized-email validation, and scoped lookup primitives in `packages/reality-core/src/reality/services/memberships.py`
- [x] T013 [FR-010] [FR-018] [DR-006] Implement redacted tenant/subject/outcome audit and atomic delivery-enqueue primitives in `packages/reality-core/src/reality/services/memberships.py` and `packages/reality-core/src/reality/services/notifications.py`

## Phase 3: User Story 1 — Invite and Join a Company (P1)

**Goal**: An owner invites either account type through one private flow; a matching
verified recipient explicitly accepts before membership and access exist.

**Independent test**: Complete new- and existing-account flows with identical owner
state, disabled public signup, explicit acceptance, and blocked mismatched/suspended/
rejected accounts.

- [x] T014 [P] [US1] [FR-001] [FR-002] [FR-003] [FR-005] [FR-026] [FR-027] [FR-032] Add failing owner/non-owner, uniform-account-path, normalization, explicit-acceptance, wrong-email, and blocked-account service stories in `packages/reality-core/tests/test_membership_invitations.py`
- [x] T015 [P] [US1] [FR-004] [FR-031] Add failing invite-bound signup/verification tests proving disabled-public-signup access, existing AccessApplication approval reason, zero duplicate application, and zero admission-slot claim in `packages/reality-core/tests/test_user_access.py`
- [x] T016 [P] [US1] [FR-003] [FR-004] [FR-005] [FR-020] Add failing inspect/signup/verify/accept HTTP contract and token-redaction tests in `packages/reality-core/tests/test_user_access.py`
- [X] T017 [P] [US1] [FR-019] [FR-020] [FR-035] Add failing contextual name/email escaping, sanitized diagnostic, locale fallback, report link, fragment URL, and no-token-log email tests in `packages/reality-core/tests/test_email_delivery.py`
- [x] T018 [US1] [FR-001] [FR-002] [FR-003] [FR-005] [FR-007] [FR-008] [FR-027] [FR-032] Implement neutral account-independent owner invitation creation, trim/casefold normalization, and atomic matching-account acceptance in `packages/reality-core/src/reality/services/memberships.py`
- [x] T019 [US1] [FR-004] [FR-005] [FR-031] Refactor invite-aware signup, verification, pending AccessApplication approval, and acceptance admission into shared behavior in `packages/reality-core/src/reality/web/auth.py` and `packages/reality-core/src/reality/services/memberships.py`
- [x] T020 [US1] [FR-003] [FR-004] [FR-005] [FR-020] Expose public-safe invitation inspect, invite signup, verification continuation, and POST acceptance in `packages/reality-core/src/reality/web/auth.py` and permit only required invite paths in `packages/reality-core/src/reality/web/app.py`
- [x] T021 [P] [US1] [FR-019] [FR-020] Implement the escaped localized invitation template and fragment link in `packages/reality-core/src/reality/web/email.py`
- [x] T022 [US1] [FR-003] [FR-004] [FR-020] [FR-033] Add Product Web invitation routing, fragment scrubbing, session-scoped reload recovery/cleanup, sign-in/signup/verification continuation, and explicit acceptance in `apps/web/src/Auth.tsx` and `apps/web/src/api.ts`
- [x] T023 [US1] [FR-019] Add English, German, Dutch, and Spanish invitation-flow strings in `apps/web/src/localization.tsx`
- [X] T024 [US1] [FR-001] [FR-002] [FR-003] [SC-002] Run the independent new/existing recipient story, measure the delivered-link-to-open-company path against the five-minute target excluding verification-email wait, and record evidence in `specs/035-company-membership-invitations/quickstart.md`

## Phase 4: User Story 2 — Manage Invitations (P1)

**Goal**: Owners list, resend, revoke, expire, and recover delivery without account
disclosure or inconsistent concurrent state.

**Independent test**: Exercise duplicate, expiry, cooldown, resend, revoke, delivery
failure/retry, stale generation, and accept races.

- [X] T025 [P] [US2] [FR-006] [FR-007] [FR-009] [FR-011] [FR-012] [FR-030] Add failing invitation lifecycle, bounded list, duplicate, expiry, cooldown, rolling invite/resend limits, revoke, and latest-generation service tests in `packages/reality-core/tests/test_membership_invitations.py`
- [X] T026 [P] [US2] [FR-008] [FR-009] [FR-012] Add failing multi-session invite uniqueness, accept/accept, accept/resend, and accept/revoke concurrency tests in `packages/reality-core/tests/test_postgresql_integration.py`
- [X] T027 [P] [US2] [FR-010] [FR-018] [FR-019] [FR-020] [FR-028] [FR-029] Add failing atomic enqueue/rollback, double-claim, lease recovery, 24-hour terminal failure, worker outage, 90-day cleanup exclusion, sanitized failure, duplicate mail, and stale-link tests in `packages/reality-core/tests/test_email_delivery.py` and `packages/reality-core/tests/test_postgresql_integration.py`
- [x] T028 [US2] [FR-006] [FR-007] [FR-009] [FR-011] [FR-012] [FR-030] Implement expiry transition, bounded access list, neutral duplicate, rolling invite/resend limits, resend cooldown/generation, and revoke in `packages/reality-core/src/reality/services/memberships.py`
- [x] T029 [US2] [FR-010] [FR-018] [FR-020] [FR-028] [FR-029] Implement due delivery claim/lease, in-memory token issuance, increasing 24-hour retry, worker-outage state, terminal failure, 90-day terminal cleanup, stale generation, and sanitized outcomes in `packages/reality-core/src/reality/services/notifications.py`
- [x] T030 [US2] [FR-010] [FR-019] Add the invitation notification worker command and Compose process in `packages/reality-core/src/reality/cli/app.py` and `compose.yml`
- [x] T031 [US2] [FR-006] [FR-009] [FR-011] [FR-012] Expose owner-only members/invitations list, resend, and revoke routes in `packages/reality-core/src/reality/web/api.py`
- [x] T032 [US2] [FR-006] [FR-009] [FR-010] [FR-011] [FR-012] [FR-028] [FR-034] Add owner invitation list/status/actions and accessible pending/failed/recovery states in `apps/web/src/App.tsx`, `apps/web/src/api.ts`, and `apps/web/src/companies.css`
- [X] T033 [US2] [FR-006] [FR-008] [FR-009] [FR-010] [FR-012] Run the invitation-management and delivery-recovery story and record evidence in `specs/035-company-membership-invitations/quickstart.md`

## Phase 5: User Story 3 — Review and Switch Company Access (P2)

**Goal**: Access is understandable and the switcher reflects active membership only.

**Independent test**: Use two identically named companies, remove one membership, and
observe explicit context, safe fallback, and zero cross-tenant disclosure.

- [X] T034 [P] [US3] [FR-011] [FR-021] [FR-024] Add failing bounded member-list, identical-name tenant isolation, bootstrap role, removed-membership, and no-company API stories in `packages/reality-core/tests/test_user_access.py` and `packages/reality-core/tests/test_master_data_api.py`
- [X] T035 [P] [US3] [FR-021] [DR-005] Add failing collection/record/non-disclosure proofs for access reads in `packages/reality-core/tests/tenant_isolation/test_families.py`
- [x] T036 [P] [US3] [FR-024] [FR-025] [FR-033] [FR-034] Add failing Members-tab, owner-control visibility, invite reload cleanup, keyboard/focus, programmatic-name, live-status/error announcement, explicit company context, and stale selection source-contract expectations in `apps/web/scripts/ux-configuration-contract.test.mjs`
- [x] T037 [US3] [FR-011] [FR-021] Implement bounded tenant-scoped access summaries in `packages/reality-core/src/reality/services/memberships.py` and `packages/reality-core/src/reality/web/api.py`
- [x] T038 [US3] [FR-024] [FR-025] Add membership role to company/bootstrap results in `packages/reality-core/src/reality/web/api.py` and `apps/web/src/api.ts`
- [x] T039 [US3] [FR-011] [FR-024] [FR-025] Add the owner-visible Members settings tab, member rows, explicit company context, and stale/no-company fallback in `apps/web/src/App.tsx` and `apps/web/src/companies.css`
- [x] T040 [US3] [FR-019] [FR-024] Add localized member-list, empty, loading, denied, and removed-company recovery text in `apps/web/src/localization.tsx`
- [X] T041 [US3] [FR-021] [FR-024] Run the multi-company switch/isolation story and record evidence in `specs/035-company-membership-invitations/quickstart.md`

## Phase 6: User Story 4 — Remove and Re-invite a Member (P2)

**Goal**: An owner safely removes a non-owner and a later accepted invitation
reactivates the same membership identity.

**Independent test**: Remove, prove next-request denial with other access preserved,
re-invite, and confirm identity-preserving reactivation plus immutable audit.

- [X] T042 [P] [US4] [FR-013] [FR-014] [FR-015] [FR-016] [FR-017] Add failing owner/platform-admin/member authorization, owner-target refusal, archive, inviter-loss, session preservation, and reactivation service/API tests in `packages/reality-core/tests/test_membership_invitations.py` and `packages/reality-core/tests/test_user_access.py`
- [X] T043 [P] [US4] [FR-008] [FR-014] [FR-015] Add failing remove/reinvite and remove/in-flight-access PostgreSQL concurrency proofs in `packages/reality-core/tests/test_postgresql_integration.py`
- [X] T044 [P] [US4] [FR-018] Add failing remove/reactivate audit identity, actor, outcome, UTC, tenant, and redaction assertions in `packages/reality-core/tests/test_membership_invitations.py`
- [x] T045 [US4] [FR-013] [FR-014] [FR-015] [FR-016] [FR-017] Implement owner/platform-admin removal, owner-target refusal, next-request semantics, and identity-preserving reactivation in `packages/reality-core/src/reality/services/memberships.py`
- [x] T046 [US4] [FR-013] [FR-014] Expose confirmed non-owner removal through `packages/reality-core/src/reality/web/api.py` and `apps/web/src/App.tsx`
- [X] T047 [US4] [FR-013] [FR-014] [FR-015] [FR-018] Run the removal/reactivation/session story and record evidence in `specs/035-company-membership-invitations/quickstart.md`

## Phase 7: User Story 5 — Safe Cross-Interface Membership Actions (P3)

**Goal**: Internal Chat uses the same owner-authorized operations with effect-free
preview and explicit confirmation; omitted adapters cannot bypass the boundary.

**Independent test**: Propose and approve each Chat mutation, reject/replay it, remove
owner authority between proposal and approval, and prove no external MCP/CLI exposure.

- [X] T048 [P] [US5] [FR-022] [FR-023] Add failing invite/resend/revoke/remove proposal, reject, replay, approval, stale target, and owner-reauthorization tests in `packages/reality-core/tests/test_application_tools.py`
- [X] T049 [P] [US5] [FR-021] [FR-022] [FR-023] Add failing Chat API actor propagation, foreign-tenant, no-confirmation, and no-effect assertions in `packages/reality-core/tests/test_ai_mcp.py` and `packages/reality-core/tests/test_master_data_api.py`
- [X] T050 [P] [US5] [FR-022] Add failing command-catalog parity and explicit external-MCP/local-CLI omission assertions in `packages/reality-core/tests/test_application_catalog.py` and `packages/reality-core/tests/test_ai_mcp.py`
- [X] T051 [US5] [FR-022] [FR-023] Implement membership mutation handlers and server-derived proposal summaries in `packages/reality-core/src/reality/tools/application.py`
- [X] T052 [US5] [FR-021] [FR-023] Pass the authenticated confirming principal through Chat proposal approval and reauthorize on execution in `packages/reality-core/src/reality/web/api.py` and `packages/reality-core/src/reality/tools/application.py`
- [X] T053 [US5] [FR-022] Register Web/API/Chat commands, confirmation policy, reads/writes, and deliberate MCP/CLI omission in `packages/reality-core/config/command_catalog.yaml`
- [X] T054 [US5] [FR-022] [FR-023] Run the cross-interface proposal/confirmation story and record evidence in `specs/035-company-membership-invitations/quickstart.md`

## Final Phase: Cross-Cutting Documentation, Verification, and Review

- [x] T055 [P] [FR-019] [FR-024] [FR-034] [FR-035] Add and audit all EN/DE/NL/ES strings, contextual escaping, responsive states, keyboard labels, visible focus, programmatic names, and screen-reader status/error semantics in `apps/web/src/localization.tsx`, `apps/web/src/companies.css`, and `apps/web/src/auth.css`
- [x] T056 [P] [FR-001] [FR-013] [FR-021] [FR-025] [DR-001] [DR-005] Update durable tenancy, Web, test, and data-model contracts in `docs/features/tenancy.md`, `docs/WEB_SPEC.md`, `docs/TEST_STRATEGY.md`, and `docs/DATA_MODEL.md`
- [x] T057 [P] [FR-010] [FR-019] [FR-020] [FR-028] [FR-029] Document notification-worker operation/outage, 24-hour retry, 90-day cleanup, observability, provider ambiguity, and secret handling in `apps/docs/content/operations/deployment.md`
- [X] T058 [FR-001–FR-035] [DR-001–DR-006] Run `make spec-check` and audit every requirement against scenarios, tests, implementation tasks, and `specs/035-company-membership-invitations/checklists/access-security.md`
- [x] T059 [DR-002] [DR-003] [DR-004] Run migration fresh-upgrade/guarded-downgrade and real PostgreSQL concurrency suites defined in `specs/035-company-membership-invitations/quickstart.md`
- [x] T060 Run `make lint` and the complete backend PostgreSQL suite with `make test`, recording results in `specs/035-company-membership-invitations/quickstart.md`
- [X] T061 [FR-019] [FR-024] Run `make web-build`, `cd apps/web && npm run i18n:audit`, frontend contract tests, and manual EN/DE/NL/ES desktop/mobile review; record results in `specs/035-company-membership-invitations/quickstart.md`
- [X] T062 [FR-001–FR-035] [DR-001–DR-006] Review the final diff against the Constitution, approved Spec/Plan, shortest links, tenant boundaries, token secrecy, audit durability, migration safety, and unrelated concurrent work in `specs/035-company-membership-invitations/checklists/requirements.md`
- [X] T063 Record final product-owner/reviewer acceptance and update only verified tasks/checklists and any applicable `docs/V0_CHECKLIST.md` item after every required gate is green in `specs/035-company-membership-invitations/checklists/requirements.md`

## Dependencies

- Phase 1 blocks all implementation; T004 (`$speckit-analyze`) must have no CRITICAL finding.
- Phase 2 blocks every story because all use the shared schema, principal, audit, and enqueue primitives.
- US1 is the MVP and blocks US2 recipient recovery, US3 member presentation, and US4 reactivation.
- US2 depends on US1 invitation creation/acceptance and completes resend/revoke/delivery.
- US3 depends on foundational access reads; it may proceed alongside US2 after US1.
- US4 depends on US1 acceptance/reactivation primitives; it may proceed alongside US2/US3.
- US5 depends on completed shared mutations from US1, US2, and US4.
- Final verification depends on all selected stories.

## Parallel Execution Examples

- After Phase 1, T005–T007 can proceed in parallel before T008–T013.
- US1: T014–T017 can proceed in parallel; T021/T023 can proceed once contracts settle.
- US2: T025–T027 can proceed in parallel; Web T032 can follow API contract T031 while worker T029–T030 proceeds separately.
- US3: T034–T036 can proceed in parallel; localized UI T040 can follow result shapes.
- US4: T042–T044 can proceed in parallel before T045–T046.
- US5: T048–T050 can proceed in parallel before tool/API/catalog implementation.
- Final documentation T055–T057 can proceed in parallel before gates T058–T063.

## Implementation Strategy

1. **MVP**: Phases 1–3 deliver owner invite plus explicit acceptance for new/existing
   accounts with durable intent and no direct membership administration UI beyond the
   invitation entry point.
2. **Operational invitation management**: Phase 4 adds list/resend/revoke and reliable
   worker recovery.
3. **Access visibility and lifecycle**: Phases 5–6 add member settings, switching,
   removal, and reactivation.
4. **Interface parity**: Phase 7 adds confirmed internal Chat without weakening owner
   identity; MCP/CLI remain intentionally omitted.
5. **Completion**: Run all gates and reviews; never mark tasks/checklists complete while
   required evidence is red.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-003 | T014, T016 | T018, T020, T024, T056 | Complete |
| FR-004–FR-005 | T015–T016 | T019–T020 | Complete |
| FR-006–FR-012 | T025–T027 | T028–T033 | Complete |
| FR-013–FR-017 | T042–T044 | T045–T047, T056 | Complete |
| FR-018 | T006, T027, T044 | T008–T009, T013, T029 | Complete |
| FR-019–FR-020 | T017, T027 | T021–T023, T029–T030, T055, T057, T061 | Complete |
| FR-021 | T007, T034–T035, T049 | T011–T013, T037, T045, T052, T056 | Complete |
| FR-022–FR-023 | T048–T050 | T051–T054 | Complete |
| FR-024–FR-025 | T034, T036 | T038–T041, T055–T056, T061 | Complete |
| FR-026 | T014 | T012, T018 | Complete |
| FR-027, FR-031–FR-032 | T014–T015 | T018–T019 | Complete |
| FR-028–FR-030 | T025, T027 | T028–T030, T032, T057 | Complete |
| FR-033–FR-035 | T017, T036 | T021–T023, T032, T055, T061 | Complete |
| DR-001–DR-006 | T005–T007 and story isolation/audit tests | T008–T013, T056, T058–T062 | Complete |
