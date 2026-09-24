---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Decision Trail

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Paths are relative to the repository root; `core/` abbreviates
`packages/reality-core/` and `web/` abbreviates `apps/web/`.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement appears in at least one test task and one implementation
or documentation task. Test tasks precede the code they prove and are observed failing first.

## Phase 1: Specification and Design Gates

- [X] T001 Confirm owner approval of scope and the two MCP attribution decisions, and absence of clarification markers in `specs/263-decision-trail/spec.md`
- [X] T002 Confirm every Constitution Check row is PASS and the two-column schema expansion is justified in `specs/263-decision-trail/plan.md`
- [X] T003 Cross-check reuse of specs 054, 055 and 211 and record decisions in `specs/263-decision-trail/research.md`
- [X] T004 Run the analysis pass and resolve every CRITICAL or HIGH finding across `specs/263-decision-trail/` (findings A1–A6 in `research.md`)

## Phase 2: Foundational — Schema and Attribution Reader

**Goal**: The two nullable columns and the one reader every story renders through.

### Tests

- [X] T005 [P] [DR-002] Add a failing upgrade/downgrade test for `0093_decision_trail` asserting both columns, the composite FK and both indexes, and no data rewrite, in `core/tests/test_decision_trail_migration.py`
- [X] T006 [P] [DR-003] Add failing tests for `decision_attributions`: person, MCP token with issuer, legacy token (issuer unknown), revoked token, pre-055 decision, pending decision; plus a cross-tenant case where a token or user of another company is never resolved, in `core/tests/test_decision_attribution.py`
- [X] T007 [P] [DR-003] Add a statement-count assertion (≤ 3 statements for 1 and for 100 proposals) in `core/tests/test_decision_attribution.py`

### Implementation

- [X] T008 [DR-002] Add `MCPAccessToken.created_by_user_id` and `ChangeProposal.decided_via_token_id` with composite FK `(tenant_id, decided_via_token_id)` → `mcp_access_token(tenant_id, id)` in `core/src/reality/db/core.py`
- [X] T009 [DR-002] Write migration `core/migrations/versions/0093_decision_trail.py` (additive, nullable, one index per FK first column, reversible, no backfill)
- [X] T010 [DR-003] [DR-004] Implement `decision_attributions(session, tenant_id, proposal_ids)` in `core/src/reality/services/decision_attribution.py`, resolving names only for users who decided a proposal or issued a token of the tenant
- [X] T011 [DR-003] Register `reality.services.decision_attribution:decision_attributions` under `explicit_operations` and classify it in `core/config/tenant_isolation_catalog.yaml`; bump the pinned count in `core/tests/test_application_catalog.py` only if the test requires it
- [X] T012 [P] Account for the derived `ix_action_decided_via_token_id` through `0093_decision_trail.INDEXES` in `core/tests/test_schema_indexes.py` (the table stays fully checked rather than being listed in `later_tables`)
- [X] T013 [P] Mention `test_decision_trail_migration.py`, `test_decision_attribution.py`, `test_decision_trail_mcp.py`, `test_decision_trail_events.py` under a spec 263 section of `docs/SPEC_COVERAGE_MATRIX.md`

**Checkpoint**: T005–T007 green; `pytest core/tests/test_application_catalog.py core/tests/tenant_isolation core/tests/test_schema_indexes.py core/tests/test_reporting_graph_coverage.py` green.

## Phase 3: User Story 1 — Know who confirmed through an agent (P1)

**Goal**: Every decision settled through MCP records its token; newly issued tokens name their issuer.

**Independent test**: Issue a token as an owner, propose and confirm through the MCP runtime, read the decision.

### Tests

- [X] T014 [P] [US1] [FR-001] Add a failing test that `POST /settings/mcp/tokens` records the signed-in owner as issuer, and that a token created without a user (CLI/test path) records none, in `core/tests/test_decision_trail_mcp.py`
- [X] T015 [P] [US1] [FR-002] [FR-003] Add failing MCP runtime tests (`proposal_approve_and_execute`, `proposal_reject`) asserting `decided_via_token_id` is the calling token, `decided_by_user_id` stays null, and `decided_at` is set, for a web-issued and a legacy token, in `core/tests/test_decision_trail_mcp.py`
- [X] T016 [P] [US1] [FR-002] Add failing tests that every reset to `proposed` (review failure, analytics refusal, reviewed-handler refusal) clears `decided_via_token_id`, in `core/tests/test_decision_trail_mcp.py`
- [X] T017 [P] [US1] [FR-004] Add a failing test that the MCP approve/reject results carry `decider` with `kind: "mcp_token"`, and that revoking the token afterwards yields `revoked: true` on re-read, in `core/tests/test_decision_trail_mcp.py`
- [X] T018 [US1] [DR-005] Keep the web approval path as an unchanged control: signed-in approval records the person and no token; existing approval-permission tests in `core/tests/test_application_tools.py` stay green unmodified

### Implementation

- [X] T019 [US1] [FR-001] Add `issued_by_user_id` to `create_mcp_access_token` in `core/src/reality/mcp/auth.py` and pass the owner from `post_mcp_token` in `core/src/reality/web/api.py`
- [X] T020 [US1] [FR-002] Add the `SETTLING_TOKEN` ContextVar in `core/src/reality/mcp/catalog.py`, set and reset it around `dispatch_tool` in `core/src/reality/mcp/server.py` from `access_token.client_id`
- [X] T021 [US1] [FR-002] [FR-003] Add `settling_token_id` to `approve_and_execute_proposal` and `reject_proposal`, record it in `_record_decision`, the finance branch and the claim `UPDATE`, and clear it in every reset, in `core/src/reality/tools/application.py`; pass it from `_approve_proposal` / `_reject_proposal` in `core/src/reality/mcp/catalog.py`
- [X] T022 [US1] [FR-004] Return `decider` from the MCP approve/reject handlers via `decision_attributions` in `core/src/reality/mcp/catalog.py`; pass the calling token only when it belongs to the company, so an approval never fails on its attribution

**Checkpoint**: US1 tests green; MCP runtime suite `core/tests/test_mcp_http_runtime.py` and `core/tests/test_ai_mcp.py` green.

## Phase 4: User Story 2 — Every confirmed change leads back to its decision (P1)

**Goal**: Every event written while a proposal executes references it, for the whole mutating catalog.

**Independent test**: Confirm one proposal per affected family and read its events.

### Tests

- [ ] T023 [P] [US2] [FR-005] Add failing unit tests for the executing-proposal scope in `core/tests/test_decision_trail_events.py`: default fills `action_id`; an explicit id is kept unchanged, equal or different; another tenant's scope is ignored; the scope is reset after an exception
- [ ] T024 [P] [US2] [FR-005] Add failing regressions for `payment_term_create`, `price_list_create`, `price_tier_create` and `party_price_list_assign` through a confirmed proposal, asserting every written event references it, in `core/tests/test_decision_trail_events.py`
- [ ] T025 [US2] [FR-006] Add the catalog guard in `core/tests/test_decision_trail_events.py`: a temporary mutating tool emitting without `action_id` is linked through the generic, master-tool and finance branches; every mutating tool in `TOOLS` is routed through one of those branches; a control emission outside the scope stays unlinked
- [ ] T026 [US2] [DR-005] Run the playground decision suite `core/tests/test_playground_security.py` before implementation to record its baseline

### Implementation

- [ ] T027 [US2] [FR-005] Add `executing_proposal(tenant_id, proposal_id)` and the default logic (explicit id wins) before `require_decision_action` in `emit_business_event`, in `core/src/reality/services/core.py`; classify the new public function in `core/config/tenant_isolation_catalog.yaml`
- [ ] T028 [US2] [FR-005] [FR-006] Route every handler invocation of `approve_and_execute_proposal` (finance command, analytics request/change, master tools, generic) through one `_run_handler` inside the scope in `core/src/reality/tools/application.py`
- [ ] T029 [US2] [FR-005] Review every `action_id=` call site reachable from `approve_and_execute_proposal` and confirm it passes the executing proposal; review every existing test that now sees a non-null `action_id`; update only assertions that pinned the defect, and list them in the PR body

**Checkpoint**: US2 tests green; `core/tests/test_playground_security.py` matches the T026 baseline.

## Phase 5: User Story 3 — Reopen a settled decision (P2)

**Goal**: The Decisions page shows the 054/055 register with the FR-004 decider and opens any decision by id.

### Tests

- [ ] T030 [P] [US3] [FR-007] [FR-004] Add failing history payload tests for person, MCP and unknown `decider` in `core/tests/test_daily_work_lists.py`
- [ ] T031 [P] [US3] [FR-008] Add a failing test that `GET /change-proposals/{id}/review` returns `decided_at` and `decider` for executed, rejected and pending decisions, in `core/tests/test_proposal_review_parity.py`
- [ ] T032 [P] [US3] [FR-008] Add a failing test that `proposal_execution_status` returns `decision` in `core/tests/test_decision_trail_mcp.py`
- [ ] T033 [P] [US3] [FR-007] [FR-008] Add a failing web contract `web/scripts/decision-history.test.mjs`: Pending/History tabs, `tab` and `decision` URL parameters, register columns (requested, action, scope, requester, outcome, decider, decided at), paging per 054 FR-006–FR-010 with at most 25 rows per page

### Implementation

- [ ] T034 [US3] [FR-007] Embed `decider` in `_proposal_payload` in `core/src/reality/web/api.py`
- [ ] T035 [US3] [FR-008] Embed `decided_at` and `decider` in `proposal_review` in `core/src/reality/services/proposal_reviews.py` and `decision` in `_proposal_execution_status` in `core/src/reality/tools/application.py`
- [ ] T036 [US3] [FR-007] [FR-008] Add the `decider`/`decision` types and the `tab`/`decision` route parameters in `web/src/api.ts` and `web/src/unified/routing.ts`
- [ ] T037 [US3] [FR-007] [FR-008] Add the History tab and the single-decision view to `web/src/unified/DecisionsPage.tsx`, reusing the existing argument presentation and `WorkList` components
- [ ] T038 [US3] [FR-004] Add the shared `web/src/unified/DecisionLine.tsx` rendering person, token-and-issuer and unknown deciders

## Phase 6: User Story 4 — See the decision on the record and in Activities (P2)

### Tests

- [ ] T039 [P] [US4] [FR-009] [FR-011] Add failing provenance tests: origin of a record created through a decision carries `decision`; a record without one carries none; a pre-055 decision reads the decider as unknown; a record created without a decision and later updated through one names no creating decision, in `core/tests/test_provenance.py`
- [ ] T040 [P] [US4] [FR-010] [FR-011] Add a failing test that `timeline_activity` items with `action_id` carry `decision` and others do not, within the existing statement budget, in `core/tests/test_decision_trail_events.py`
- [ ] T041 [P] [US4] [FR-009] [FR-010] Add a failing web contract `web/scripts/decision-line.test.mjs` for `SourceBadge` and `ActivityDrawer`: decision line with link, no line without a decision, no bare "Action ID" as primary presentation

### Implementation

- [ ] T042 [US4] [FR-009] Replace `_deciding_actors` with `_creating_decisions` and add `decision` to `record_origins`, keeping `actor`, in `core/src/reality/services/provenance.py`
- [ ] T043 [US4] [FR-010] Add batched `decision` to `timeline_activity` in `core/src/reality/services/core.py`
- [ ] T044 [US4] [FR-009] [FR-010] [FR-011] Render `DecisionLine` in `web/src/unified/SourceBadge.tsx` and `web/src/unified/ActivityDrawer.tsx`, linking to `/app/decisions?decision=<id>`

## Phase 7: Localization, Documentation and Verification

- [ ] T045 [FR-012] Add German, Dutch and Spanish entries for every new string in `web/src/localization.tsx` (German: Entscheidung, bestätigt von, bestätigt über Token, ausgestellt von, unbekannt, widerrufen; du/je/tú register), and run `cd web && npm run i18n:audit`
- [ ] T046 [P] [FR-004] Add a browser script `web/scripts/decision-trail-browser.mjs`: open an item created through an MCP decision, follow its decision link, verify the History row
- [ ] T047 [P] Update `docs/WEB_SPEC.md` (Decisions history, decision line on origin and activities) and the MCP attribution note in `docs/features/` where MCP tokens are described
- [ ] T048 Run `make docs-generate` and commit generated Tool Usage output; run `make docs-catalog-check`
- [ ] T049 Run `make spec-check`, `make lint` (ruff from `core/` with `--no-cache`), `make test`, `make web-build`, `cd web && npm run test:contracts`
- [ ] T050 [SC-001] [SC-002] Re-run the agent setup against a fresh company and record the `quickstart.md` query results in `specs/263-decision-trail/quickstart.md`
- [ ] T051 Review the final diff against spec, Constitution and wording rule ("confirmed through token", never "confirmed by" the issuer); mark tasks complete only with green evidence

## Dependencies

- Phase 2 blocks all stories. US1 and US2 are independent of each other.
- US3 and US4 render `decider`/`decision` from Phase 2 and show MCP attribution only after US1; US4's record links require US2 for the formerly unlinked families.
- Suggested MVP: Phase 2 + US1 + US2 (everything that cannot be recovered later).

## Requirement Coverage

| Requirement | Test tasks | Implementation tasks |
|---|---|---|
| FR-001 | T014 | T019 |
| FR-002 | T015, T016 | T020, T021 |
| FR-003 | T015 | T021 |
| FR-004 | T017, T030, T046 | T022, T038 |
| FR-005 | T023, T024 | T027, T028, T029 |
| FR-006 | T025 | T028 |
| FR-007 | T030, T033 | T034, T036, T037 |
| FR-008 | T031, T032, T033 | T035, T036, T037 |
| FR-009 | T039, T041 | T042, T044 |
| FR-010 | T040, T041 | T043, T044 |
| FR-011 | T039, T040, T041 | T042, T043, T044 |
| FR-012 | T045 (audit) | T045 |
| DR-001 | T024, T005 (no record-table column) | T027, T028 |
| DR-002 | T005 | T008, T009 |
| DR-003 | T006, T007 | T010, T011 |
| DR-004 | T006, T041 | T010, T042, T043 |
| DR-005 | T018, T026 | T021, T028 (no permission change) |
| SC-001, SC-002 | T050 | — |
| SC-003 | T046 | T037, T044 |
| SC-004 | T006, T039 | T010 |
| SC-005 | T005 | T009 |
| SC-006 | T045, T049 | — |
