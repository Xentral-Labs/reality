---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Every business company knows its own business partner

**Input**: `spec.md`, `plan.md`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

`core/` stands for `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Close clarification markers in `specs/289-costing-ready-companies/spec.md` (owner decisions 2026-09-27)
- [x] T002 All Constitution Check rows PASS in `specs/289-costing-ready-companies/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings (2026-09-27: none CRITICAL; A1–A4 resolved, see plan "Analysis")

## Phase 2: User Story 1 — new companies (P1)

- [ ] T004 [P] [US1] [FR-001] [FR-002] [FR-003] [DR-001] Write failing tests in
  `core/tests/test_company_party.py`:
  - `::test_business_company_records_its_partner`;
  - `::test_replayed_creation_keeps_one_partner`;
  - `::test_creation_source_states_the_requested_name`;
  - `::test_sandbox_demo_and_storyline_parties_are_unchanged`.

  Search the existing company setup tests for assertions that a new business company has no
  parties.
- [ ] T005 [US1] Record the company partner in the `business` branch of
  `company_setup.create_company` (`core/src/reality/services/company_setup.py`).

## Phase 3: User Story 2 — existing companies (P1)

- [ ] T006 [P] [US2] [FR-004]–[FR-006] [FR-008] [DR-003] [DR-004] Write failing tests:
  - `::test_draft_offers_the_prefilled_action`;
  - `::test_confirmed_proposal_records_through_master_data`;
  - `::test_draft_names_the_waiting_proposal`;
  - `::test_confirmation_is_refused_once_a_partner_exists`;
  - `::test_several_partners_keep_the_choice`;
  - `::test_no_party_before_confirmation`;
  - `::test_practice_company_is_not_offered_the_action`.
- [ ] T007 [US2] Implement `core/src/reality/services/company_party.py` (preview, waiting
  proposal, handler) and the tool `company_party_record` in `core/src/reality/tools/application.py`.

  New refusals are coded in `core/config/service_refusals.json`, with de/nl/es in
  `apps/web/src/localization.tsx`.
- [ ] T008 [US2] Give the `company_party_missing` input its detail (`core/src/reality/services/cost_review_draft.py`,
  `core/src/reality/domain/cost_review_draft.py`), and reword the explanation in `core/config/resolution_guidance.json`.
- [ ] T009 [US2] Add the web route `POST /api/tenants/{t}/company-party/prepare` (`core/src/reality/web/api.py`).
- [ ] T010 [US2] Add the catalog gates for the new command:
  - `command_catalog.yaml` (entry, parameter descriptions, capability guidance, agent coverage);
  - `tool_catalog.json` topics;
  - `resource_catalog.yaml` with `labels.de`;
  - `tenant_isolation_catalog.yaml` and the pinned counts;
  - `action_discovery.json`;
  - `apps/web/scripts/fixtures/action-reference.json`.

## Phase 4: User Story 3 — chat and MCP (P2)

- [ ] T011 [P] [US3] [FR-007] Write failing `::test_mcp_draft_and_propose_parity` (draft input
  and `company_party_record_propose`).
- [ ] T012 [US3] Add `company_party_record_propose` to `core/src/reality/mcp/catalog.py`
  (`application_name`), then run `make docs-generate`.

## Phase 5: Web

- [ ] T013 [P] [FR-004] [FR-006] Write failing `apps/web/scripts/company-party-contract.test.mjs`:
  - the button posts the prepare route;
  - the waiting link uses `proposal_id`;
  - no name is sent from the client.
- [ ] T014 Add the button, the prefilled name, the waiting link and de/nl/es in
  `apps/web/src/unified/CostReviewDraftDialog.tsx` and `apps/web/src/api.ts`.
- [ ] T015 Browser proof: write `apps/web/scripts/company-party-browser.mjs` (de/nl/es, 390 and
  1440 px) and add it to `apps/web/scripts/browser-suite.json`.

## Final Phase

- [ ] T900 `make spec-check`, and the check with `PR_BODY` and `--base-ref origin/main`; add
  the new test families to `docs/SPEC_COVERAGE_MATRIX.md`.
- [ ] T901 Run Ruff on my own files only (`--no-cache`) and the complete backend suite (CI).
- [ ] T902 `make web-build`, i18n audit, node contracts, browser suite.
- [ ] T903 `make docs-generate` and `make docs-catalog-check`.
- [ ] T904 [SC-001] [SC-002] Live walk-through on an isolated stack (`quickstart.md`).
- [ ] T905 Update `docs/features/company-setup-demo.md` and `docs/features/master_data.md`.
- [ ] T906 Review the final diff against the Constitution and every FR and DR.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T004 | T005 | Pending |
| FR-002 | T004 | T005 | Pending |
| FR-003 | T004 | T005 | Pending |
| FR-004 | T006, T013 | T007, T008, T014 | Pending |
| FR-005 | T006 | T007 | Pending |
| FR-006 | T006, T013 | T007, T008, T014 | Pending |
| FR-007 | T011 | T008, T012 | Pending |
| FR-008 | T006 | T008 | Pending |
| DR-001 | T004 | T005 | Pending |
| DR-002 | T906 | — | Pending |
| DR-003 | T006, T011 | T007, T009, T012 | Pending |
| DR-004 | T006 | T007 | Pending |
| SC-001 | T904 | — | Pending |
| SC-002 | T904 | — | Pending |
