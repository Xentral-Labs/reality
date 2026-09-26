---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Guidance for missing basis

**Input**: `spec.md`, `plan.md`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Paths below are relative to the repository root; `core/` stands for
`packages/reality-core/`.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review and close clarification markers in `specs/279-missing-basis-guidance/spec.md` (owner accepted scope 2026-09-26)
- [x] T002 Confirm all Constitution Check rows are PASS in `specs/279-missing-basis-guidance/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings (2026-09-26: no CRITICAL findings; fixed:
  - edge cases "state changes while open" and "no AI credentials" had no task (now T024/T027);
  - SC-001 lacked a browser sweep beyond the cost panel (T908);
  - SC-003 lacked contribution evidence (T909);
  - T023 was ordered after the task that needs it;
  - US5 scenario 2 promised an order prefill the form does not support;
  - the plan used a private contribution helper instead of `costing.contribution_preview`.)

## Phase 2: Foundation — catalog and builder (blocks all stories)

- [x] T004 [P] [FR-004] Write failing `core/tests/test_resolution_guidance.py`:
  - catalog loads and validates;
  - an unknown form, a role outside the closed set, a missing `{scope}` and a dangling blocker step are each rejected, with a valid-catalog positive control;
  - `EMITTED_CODES ⊆ catalog`.
- [x] T005 [P] [FR-004] Write failing `apps/web/scripts/resolution-guidance-localization.test.mjs`: every catalog label, explanation, alternative label and chat prompt has de/nl/es translations (pattern: `action-discovery-localization.test.mjs`).
- [x] T006 [FR-001] Create `core/config/resolution_guidance.json`:
  - reasons for every cost `missing_basis`, receipt-level and census code, guidance stage, projection state, carrying-value state, `no_applicable_price`, and the fulfillment blockers;
  - steps `receipt_cost_evidence`, `inventory_review`, `inventory_review_renew`, `contribution_review`, `selling_cost_review`, `owner_confirmation`, `system_status`, the form steps, and `source_data_limit`.
- [x] T007 [FR-001] Implement `core/src/reality/domain/resolution_guidance.py`: step/guidance builder, closed role/path/state sets, `EMITTED_CODES`, and `validate_resolution_guidance(catalog, forms)`.
- [x] T008 [FR-004] Load, validate and serve the catalog as `resolution_guidance` in `core/src/reality/catalogs.py` (next to `discovery`). Add `label` and `clears_through` to `operational_exception_classes` there.
- [x] T009 [FR-004] Add de/nl/es translations for all catalog strings to `apps/web/src/localization.tsx` (ERP vocabulary per `docs/features/shared-language.md`), and add types to `apps/web/src/api.ts`.

## Phase 3: User Story 1 — plain language (P1)

- [x] T010 [P] [US1] [FR-005] [FR-006] Write failing `apps/web/scripts/resolution-guidance-contract.test.mjs`:
  - `ResolutionGuidance` renders labels, not codes;
  - `CostExplanation` no longer renders `guidance.reason`, `guidance.stage`, `<code>` of a tool, or raw `missing_basis` entries;
  - an unknown code renders the generic sentence.
- [x] T011 [P] [US1] [FR-012] Write failing `apps/web/scripts/exception-catalog-localization.test.mjs`: every exception class `label` and `clears_through` in `core/config/operational_exception_catalog.yaml` has de/nl/es translations.
- [x] T012 [US1] [FR-006] Implement `apps/web/src/unified/ResolutionGuidance.tsx` (reason, explanation and ordered steps; labels only; generic fallback) without action controls yet.
- [x] T013 [US1] [FR-005] Use `ResolutionGuidance` in `apps/web/src/unified/CostExplanation.tsx`:
  - remove the duplicate reason, the raw stage and the `<code>` element;
  - render the missing-basis list through catalog labels.
- [x] T014 [US1] [FR-012] Render exception titles and resolution text by `class_id` through `t()` in `apps/web/src/unified/AttentionPage.tsx`, and add the 39 labels and guidance texts to `apps/web/src/localization.tsx`. German titles reuse the existing `labels.de` entries in `core/config/resource_catalog.yaml` so both editions say the same thing.
- [x] T015 [US1] Extend `apps/web/scripts/cost-explanation-browser.mjs` with a German session asserting that no raw code is visible (SC-001 for the cost panel).

## Phase 4: User Story 2 — cost path (P1)

- [x] T016 [P] [US2] [FR-001] [FR-002] Write failing `core/tests/test_cost_resolution.py`:
  - inventory steps for uninitialized, pending, stale and complete;
  - the first open step is the receipt when a receipt lacks cost;
  - an item without receipts starts at `inventory_review`.
- [x] T017 [P] [US2] [FR-003] Add failing contribution tests to `core/tests/test_cost_resolution.py`:
  - an unreviewed item makes the inventory review the first open step;
  - a stale inventory review names the renewal;
  - `selling_costs_unknown` never blocks DB1 steps;
  - `billed_order_line_missing` yields a path-`none` step.
- [x] T018 [P] [US2] [DR-001] [DR-004] Add to `core/tests/test_cost_resolution.py`:
  - guidance writes nothing (event sequence and row counts unchanged);
  - a cross-tenant item is `NotFound`;
  - another company's proposal is ignored, paired with the own-company positive control.
- [x] T019 [P] [US2] [DR-003] Add `test_mcp_cost_query_returns_steps` and a compatibility assertion (`stage`, `reason`, `next_action` unchanged) to `core/tests/test_cost_query.py`.
- [x] T020 [US2] [FR-001] [FR-002] [FR-003] Implement `core/src/reality/services/cost_resolution.py` (`inventory_steps`, `contribution_steps`, the proposal lookup and the `writable` predicate).
- [x] T021 [US2] [FR-001] Extend `cost_guidance` in `core/src/reality/domain/cost_query.py` (`reason_code`, `steps`, `writable`, `value_reasons`), and call the resolution service from `core/src/reality/services/cost_query.py` for current reads only.
- [x] T022 [US2] [FR-010] In `apps/web/src/unified/CostExplanation.tsx`:
  - drop the inventory "Unit cost" field;
  - show the carrying-value reason from `value_reasons`;
  - render steps with done, open and blocked state;
  - keep "Inspect cost basis" when complete.
- [x] T023 [US2] (do before T020) Add a predicate `core_operation_allowed(session, tenant, operation) -> bool` beside `require_core_operation` in `core/src/reality/services/tenant_policy.py`, with a test in `core/tests/test_cost_resolution.py::test_sandbox_not_writable`.

## Phase 5: User Story 3 — act from the step (P2)

- [x] T024 [P] [US3] [FR-007] [FR-008] [FR-009] Extend `apps/web/scripts/cost-explanation-browser.mjs`:
  - the form step opens `supplier_invoice_record`;
  - the chat step fills the composer and sends no request;
  - the owner step links to Decisions with the proposal;
  - a member sees "A company owner must confirm this" and no confirm control;
  - a company that cannot confirm cost decisions shows no write path;
  - after the owner confirms, the panel re-reads and shows the value (edge case: state changes);
  - with AI not configured, the chat step opens chat showing the existing configuration notice.
- [x] T025 [P] [US3] [DR-002] Add `test_owner_step_links_proposal_id` to `core/tests/test_cost_resolution.py`.
- [x] T026 [US3] [FR-008] Carry `detail.draft` on the `reality:open-chat` event in `apps/web/src/unified/Shell.tsx`. Pass it as `initialDraft`, and make `apps/web/src/unified/ChatPage.tsx` adopt a changed `initialDraft` without sending.
- [x] T027 [US3] [FR-007] [FR-008] [FR-009] Implement `apps/web/src/unified/guidanceActions.ts` (path → handler: action discovery `open`, chat event, decisions navigation, Home), and add the controls and "who must act" sentences to `ResolutionGuidance.tsx`. Re-read the host panel's service result after a form, proposal or decision completes.

## Phase 6: User Story 4 — stored calculations (P2)

- [x] T028 [P] [US4] [FR-011] Add `test_failed_metadata_carries_failure_code` and a guidance-shape test for each state to `core/tests/test_projection_jobs.py`.
- [x] T029 [P] [US4] [FR-011] Extend `apps/web/scripts/projection-freshness-browser.mjs`:
  - uninitialized with readiness unavailable shows the sentence and the status link;
  - failed shows the failure reason label.
- [x] T030 [US4] [FR-011] Select the latest failed run's `last_error_code` in `projection_state_expressions`, and add `failure_code` and `guidance` in `projection_metadata`, both in `core/src/reality/services/projections.py`.
- [x] T031 [US4] [FR-011] Read readiness once, and render the sentence, the failure reason and the Home link in `apps/web/src/unified/ProjectionFreshness.tsx`. Add catalog reasons for the projection job error codes to `core/config/resolution_guidance.json`.

## Phase 7: User Story 5 — remaining surfaces (P3)

- [x] T032 [P] [US5] [FR-012] Add `test_cost_finding_carries_resolution` to `core/tests/test_attention_reads.py`: the item finding gets the inventory guidance, and the document-line finding gets the contribution guidance.
- [x] T033 [P] [US5] [FR-013] [FR-014] Extend `apps/web/scripts/resolution-guidance-contract.test.mjs` for blocker labels and steps, storyline check labels and the valuation explanation. Add `apps/web/scripts/price-resolution-browser.mjs` so the price determination resolves a price and shows `no_applicable_price` on 404 (`unified-inspector-browser.mjs` already fails on `origin/main`).
- [x] T034 [US5] [FR-012] Add `resolution` for the four cost classes in `core/src/reality/services/attention_reads.py::attention_detail`, and render it in `apps/web/src/unified/AttentionPage.tsx`.
- [x] T035 [US5] [FR-013] Add party and item inputs, and call `GET /prices/resolve`, in `apps/web/src/unified/ReportExplanation.tsx` and `apps/web/src/unified/ProjectionDataDialog.tsx`, with an `api.ts` client (the report data area renders `apps/web/src/unified/PriceResolution.tsx`).
- [x] T036 [US5] [FR-014] Render blocker labels and steps in `apps/web/src/unified/ReportDataTable.tsx`. Explain `unavailable` in `apps/web/src/unified/analytics/InventoryValuation.tsx`. Render check labels in `apps/web/src/unified/StorylineNarrator.tsx`. (Data sources dropped from scope: "No import job" is information, not a missing prerequisite.)

## Final Phase: Cross-Cutting Review

- [x] T900 Run the spec and traceability audit (`make spec-check`).
- [x] T901 Run Ruff (from `packages/reality-core`, `--no-cache`) and the complete backend PostgreSQL suite from a clean detached worktree. (2026-09-26: 4438 passed, 10 skipped, 3 failed under `-n 6`: the coverage-matrix check, fixed by the next commit, and two wall-clock budgets outside this feature, `test_reality_gap_replay_resumes_ten_thousand_sources_without_duplicates` and `test_live_creation_api_connects_and_starts_without_extra_requests`; all three pass alone on the final commit.)
- [x] T902 Run `make web-build`, `npm run i18n:audit`, `npm run test:contracts`, `test:cost-explanation-browser` and `projection-freshness-browser.mjs`.
- [x] T903 Confirm there is no migration (DR-005).
- [ ] T908 [SC-001] Add a German no-raw-code sweep to `apps/web/scripts/unified-operations-browser.mjs` covering Exceptions, Finance open items, Orders, Inventory valuation and the Dispatch/blockers report (the cost panel is covered by T015).
- [ ] T909 [SC-003] Walk quickstart check 3 for a contribution line (member → chat → owner → value) and record the result in `quickstart.md`.
- [x] T904 Measure the cost query statement count before and after on the scale fixture, and record it in `quickstart.md`.
- [x] T905 Run `make docs-generate` and `make docs-catalog-check`, and commit any regenerated output. (Generated Tool Usage output is identical to `origin/main`'s; nothing to commit.)
- [x] T906 Update `docs/WEB_SPEC.md` (a missing-basis guidance section) and `docs/features/receipt-costing.md` (the guidance steps) after the checks are green.
- [x] T907 Review the final diff against the Constitution and every FR and DR. (Found and fixed: a moving-input conflict in the contribution preview failed the whole cost read.)

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T016, T019 | T006, T007, T020, T021 | Done |
| FR-002 | T016 | T020 | Done |
| FR-003 | T017 | T020 | Done |
| FR-004 | T004, T005 | T006–T009 | Done |
| FR-005 | T010, T015 | T013 | Done |
| FR-006 | T010 | T012 | Done |
| FR-007 | T024 | T027 | Done |
| FR-008 | T024 | T026, T027 | Done |
| FR-009 | T024, T023 | T023, T027 | Done |
| FR-010 | T010, T024 | T022 | Done |
| FR-011 | T028, T029 | T030, T031 | Done |
| FR-012 | T011, T032 | T014, T034 | Done |
| FR-013 | T033 | T035 | Done |
| FR-014 | T033 | T036 | Done |
| DR-001 | T018 | T020 | Done |
| DR-002 | T025 | T020 | Done |
| DR-003 | T019 | T021 | Done |
| DR-004 | T018 | T020 | Done |
| DR-005 | T903 | — | Done |
