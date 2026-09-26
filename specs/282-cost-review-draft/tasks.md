---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Drafted cost reviews

**Input**: `spec.md`, `plan.md`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes and repository artifacts are written in English.
`core/` stands for `packages/reality-core/`.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review and close clarification markers in `specs/282-cost-review-draft/spec.md` (owner decisions 2026-09-26)
- [x] T002 Confirm all Constitution Check rows are PASS in `specs/282-cost-review-draft/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings (2026-09-26: no CRITICAL findings. Fixed: US4 and SC-002 promised zero chat questions for inventory scopes, which contradicts FR-011's per-draft method question.)

## Phase 2: Foundation (blocks all stories)

- [x] T004 [P] [FR-001] [FR-011] Write failing `core/tests/test_cost_review_draft.py::test_draft_shape_for_both_kinds`, `::test_method_choices_follow_tracking_type`.
- [x] T005 [FR-001] [FR-011] Implement `core/src/reality/domain/cost_review_draft.py`: draft and open-input shapes, the method rule (FIFO default; specific only for serial or lot tracking), and open-input codes.
- [x] T006 [FR-004] Add open-input reasons (`valuation_method`, `company_party_missing`, `receipt_cost_incomplete`, `opening_cost_missing`, `movement_unclassified`, `ownership_ambiguous`, `return_portion_undetermined`, `review_bound_exceeded`, `upstream_not_ready`) to `core/config/resolution_guidance.json` and `EMITTED_CODES`. Add `review_draft` to `PATHS` in `core/src/reality/domain/resolution_guidance.py`, and de/nl/es to `apps/web/src/localization.tsx`.

## Phase 3: User Story 1 — contribution draft (P1)

- [x] T007 [P] [US1] [FR-002] [FR-005] Write failing `core/tests/test_cost_review_draft.py::test_contribution_draft_equals_preview_values` and `::test_complete_arguments_pass_preview_cost_change` (fixtures: `test_contribution_services.prepared`).
- [x] T008 [P] [US1] [FR-004] Write a failing `::test_open_input_upstream_not_ready` (item unreviewed), plus a preview-conflict fallback test.
- [x] T009 [US1] [FR-001] [FR-002] Implement the contribution drafting in `core/src/reality/services/cost_review_draft.py`.
- [x] T010 [P] [US1] [FR-007] [DR-003] Write failing `core/tests/test_cost_review_proposal_api.py`:
  - a submit creates a `tool:cost.change` proposal;
  - a drifted draft returns `409 draft_changed`;
  - a retried `request_id` is idempotent;
  - the endpoint calls the draft service (spy).
- [x] T011 [US1] [FR-007] Implement `GET /cost-review-draft` and `POST /cost-review-proposals` in `core/src/reality/web/api.py`.
- [x] T012 [P] [US1] [FR-006] Write a failing `apps/web/scripts/cost-review-draft-contract.test.mjs`: the dialog renders catalog wording, no IDs outside System details, and submits through the endpoint only.
- [x] T013 [US1] [FR-006] [FR-007] Implement `apps/web/src/unified/CostReviewDraftDialog.tsx` and the `api.ts` clients. Switch the `contribution_review` step to path `review_draft` with a chat alternative in `core/config/resolution_guidance.json`, and handle `review_draft` in `apps/web/src/unified/ResolutionGuidance.tsx`.
- [x] T014 [US1] Write and run `apps/web/scripts/cost-review-draft-browser.mjs`:
  - the contribution dialog shows the summary;
  - it submits and the guidance shows the owner step;
  - a 409 leads to a re-draft.

## Phase 4: User Story 2 — inventory draft (P1)

- [x] T015 [P] [US2] [FR-003] [FR-005] Write a failing `::test_inventory_draft_passes_inventory_check` covering receipts with complete cost, a shipment, a customer return with a determinable portion, a supplier return, a loss and a transfer.
- [x] T016 [P] [US2] [FR-004] Write failing `::test_open_input_company_party_missing`, `::test_open_input_receipt_cost_incomplete`, `::test_open_input_movement_unclassified` and `::test_open_input_ownership_ambiguous`, each paired with a positive control.
- [x] T017 [P] [US2] [FR-010] Write a failing `::test_bounds_report_instead_of_truncate`.
- [x] T018 [US2] [FR-003] [FR-004] [FR-010] Implement the inventory drafting in `core/src/reality/services/cost_review_draft.py`: owner, currency, unit, history, classification, receipt manifests, ownership evidence and bounds.
- [x] T019 [US2] [FR-006] Switch `inventory_review` and `inventory_review_renew` to path `review_draft` in `core/config/resolution_guidance.json`. Add the method input and the movement-class summary to `CostReviewDraftDialog.tsx`, and extend `cost-review-draft-browser.mjs`.
- [x] T020 [P] [US2] [SC-003] Write `::test_demo_profile_scopes_are_drafted_equivalently`, comparing drafts with the demo seed's arguments for its reviewed items and lines.

## Phase 5: User Story 3 — opening cost evidence (P1)

- [x] T021 [P] [US3] [FR-008] [DR-005] Write failing `core/tests/test_opening_cost.py`:
  - an opening with cost links an `opening_cost_statement` SourceRecord through `Movement.source_record_id`, and the payload holds the stated values unchanged;
  - an opening without cost behaves as today;
  - a replacement opening from a movement correction carries cost;
  - cross-tenant evidence is not found, with a positive control.
- [x] T022 [US3] [FR-008] Implement `core/src/reality/services/opening_cost.py`. Accept `opening_cost` in `movement_create` (`core/src/reality/tools/application.py`), in the MCP input schema (`core/src/reality/mcp/catalog.py`) and in the delivery review preview.
- [x] T023 [P] [US3] [FR-004] [FR-008] Write failing `::test_open_input_opening_cost_missing` and `::test_opening_with_statement_is_drafted`.
- [x] T024 [US3] [FR-008] Use the statement in the inventory draft's openings (`core/src/reality/services/cost_review_draft.py`).
- [x] T025 [US3] [FR-008] Add the optional total value, currency and evidence fields to `apps/web/src/unified/OpeningStockCard.tsx`, with translations and a contract assertion.

## Phase 6: User Story 4 — chat (P2)

- [x] T026 [P] [US4] [FR-009] Write failing tests:
  - MCP `cost_review_draft` equals the service;
  - the chat tool list includes it;
  - the `cost_change_propose` capability guidance names the draft first;
  - a scripted agent tool sequence goes draft → propose with zero questions for a derivable contribution, and asks only for the method for an inventory scope (SC-002).
- [x] T027 [US4] [FR-009] Register `TOOLS["cost.review.draft"]` (`core/src/reality/tools/application.py`), the MCP definition (`core/src/reality/mcp/catalog.py`) and the chat offering (`core/src/reality/agent/mcp_chat.py`). Add the capability guidance (`core/config/command_catalog.yaml`, read: `confirmation: none`, `side_effects: none`), `mcp_topics` (`core/config/tool_catalog.json`), `tool:cost.review.draft` (`core/config/tenant_isolation_catalog.yaml`) and resource membership with `labels.de` (`core/config/resource_catalog.yaml`).

## Final Phase: Cross-Cutting Review

- [x] T900 `make spec-check`; add the new test families to `docs/SPEC_COVERAGE_MATRIX.md`.
- [x] T901 Ruff (`packages/reality-core`, `--no-cache`) and the complete backend suite from a clean detached worktree. (2026-09-26: 4513 passed, 10 skipped, 2 failed, 2 errors. Both failures were real and fixed in later commits: proposal review parity binding, and the frontend action reference fixture. Both errors were PostgreSQL "out of shared memory" during parallel schema setup; those tests pass alone.)
- [x] T902 Run the completeness gates: `test_application_catalog.py` (isolation count), `test_tool_catalog.py`, `tests/tenant_isolation`, `test_reporting_graph_coverage.py`, `test_schema_indexes.py`.
- [x] T903 `make web-build`, i18n audit, node contracts, `cost-review-draft-browser.mjs`, `cost-explanation-browser.mjs`.
- [x] T904 `make docs-generate`; commit the regenerated Tool Usage output.
- [x] T905 [SC-001] (Inventory path live-proven 2026-09-26; DB1 blocked by web invoices without a stated net, see `quickstart.md`.) Re-run `apps/web/scripts/missing-basis-walkthrough-live.mjs` in a business company on an isolated stack, extended with the dialog path. Record in `quickstart.md`.
- [x] T906 Update `docs/features/receipt-costing.md` (draft and opening cost statement) and `docs/WEB_SPEC.md` (review dialog) after the checks are green.
- [x] T907 Review the final diff against the Constitution and every FR and DR. (Fixed: literal wildcards in item references; an accidental repo-wide reformat was reverted before merge.)

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T004 | T005, T009, T018 | Done |
| FR-002 | T007 | T009 | Done |
| FR-003 | T015 | T018 | Done |
| FR-004 | T008, T016, T023 | T006, T009, T018, T024 | Done |
| FR-005 | T007, T015 | T009, T018 | Done |
| FR-006 | T012, T014 | T013, T019 | Done |
| FR-007 | T010, T014 | T011, T013 | Done |
| FR-008 | T021, T023 | T022, T024, T025 | Done |
| FR-009 | T026 | T027 | Done |
| FR-010 | T017 | T018 | Done |
| FR-011 | T004 | T005, T019 | Done |
| DR-001 | T004 (no-write) | T009, T018 | Done |
| DR-002 | T015 | T018 | Done |
| DR-003 | T010 | T011 | Done |
| DR-004 | T016, T021 | T018, T022 | Done |
| DR-005 | T021 | T022 | Done |
| SC-001 | T905 | — | Done |
| SC-002 | T026 | T027 | Done |
| SC-003 | T020 | T018 | Done |
