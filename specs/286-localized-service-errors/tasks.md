---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Service refusals speak the user's language

**Input**: `spec.md`, `plan.md`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

`core/` stands for `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Close clarification markers in `specs/286-localized-service-errors/spec.md` (codes with values, forms plus gate, chat included; owner decisions 2026-09-27)
- [x] T002 All Constitution Check rows PASS in `specs/286-localized-service-errors/plan.md`
- [ ] T003 Run `$speckit-analyze` and resolve all CRITICAL findings

## Phase 2: Foundation (blocks all stories)

- [ ] T004 [P] [FR-001] [FR-002] [DR-004] Write failing `core/tests/test_service_refusals.py`:
  - `::test_coded_refusal_carries_code_and_values`;
  - `::test_english_sentence_is_the_filled_template`;
  - `::test_message_and_code_together_is_a_type_error`;
  - `::test_values_are_only_template_placeholders`;
  - `::test_values_are_exact_strings` (`Decimal`, `int`, `date`; no rounding);
  - `::test_strict_mode_refuses_unknown_code_and_terms`, paired with the production fallback to English;
  - `::test_uncoded_refusal_is_unchanged`.
- [ ] T005 [FR-001] [FR-002] Implement `core/src/reality/domain/refusals.py`:
  - catalog load;
  - `render`;
  - `values_json`;
  - `RefusalMixin`.

  Create `core/config/service_refusals.json` (`version`, `refusals`, `terms`), and give
  `RealityError` in `core/src/reality/services/core.py` `message=None, *, code=None, values=None`.
- [ ] T006 [P] [FR-007] Write `core/tests/test_refusal_gate.py`. It checks the four gate rules
  from the plan and runs positive and negative controls on synthetic sources.
- [ ] T007 [FR-007] Add the ratchet and the planning tool:
  - Create `core/config/refusal_ratchet.json` with the 39 in-scope modules and every uncoded
    site in them.
  - Mark each entry with `scope: "286"` (reachable from the forms, per `scripts/refusal_reach.py --tight`)
    or `scope: "later"`.
  - Add `scripts/refusal_reach.py` as the advisory planning tool.
  - The gate is green with the full ratchet.

## Phase 3: Transport (US1, US3)

- [ ] T008 [P] [US1] [FR-003] Write failing API tests in `core/tests/test_service_refusals.py`:
  - `::test_api_sends_code_template_values_per_status` (400/404/409 on the delivery prepare,
    approve and master data routes; 422 `action_fields_invalid`);
  - `::test_uncoded_refusal_shape_is_unchanged`;
  - `::test_draft_changed_keeps_its_detail_object`.
- [ ] T009 [US1] [FR-003] Implement `RefusalHTTPException` in `api_error`
  (`core/src/reality/web/api.py`) and its handler (`core/src/reality/web/app.py`), and code the
  422 "Check the action fields.".
- [ ] T010 [P] [US3] [FR-004] [FR-008] Write failing tests:
  - `::test_chat_stream_error_carries_code`;
  - `::test_chat_tool_result_keeps_english_and_adds_values`;
  - `::test_mcp_error_uses_refusal_code` (class code without one; `message` unchanged);
  - `::test_failed_receipt_carries_refusal_code`.
- [ ] T011 [US3] [FR-004] [FR-008] Implement the transport in:
  - `core/src/reality/web/chat_stream.py`;
  - `core/src/reality/agent/mcp_chat.py`;
  - `core/src/reality/mcp/server.py`;
  - `core/src/reality/tools/application.py` (`_finalize_known_no_effect_failure`).

## Phase 4: Web (US1, US2, US3)

- [ ] T012 [P] [FR-005] [FR-009] Write failing `apps/web/scripts/service-refusals-contract.test.mjs`. It covers:
  - interpolation of every kind;
  - `term` values translated;
  - a missing placeholder or template falling back to `detail`;
  - English returning the English sentence;
  - no refusal-text comparison in `apps/web/src`.
- [ ] T013 [FR-005] [FR-009] Implement the web side:
  - `apps/web/src/refusals.ts`;
  - `APIError` fields and localization in `request()` and `sendChatRequest` (`apps/web/src/api.ts`);
  - `apps/web/src/unified/chatStream.ts`;
  - `ChatPage.tsx` comparing `chat_session_not_found`.
- [ ] T014 [P] [FR-006] Write failing `apps/web/scripts/service-refusals-localization.test.mjs`.
  It reads `core/config/service_refusals.json` and requires the following for every template
  and term:
  - de/nl/es entries;
  - all placeholders kept;
  - protected terms kept.

## Phase 5: Area conversions (US1, US2; one commit each)

Each task has the same steps:
- Add `code=`/`values=` at every `scope: "286"` site of its modules, one code per meaning.
- Add the catalog entries and terms.
- Add the de/nl/es translations in `apps/web/src/localization.tsx`.
- Remove the entries from the ratchet.
- Add a before/after check that the rendered English equals the former sentence for every
  converted site (`core/tests/test_service_refusals.py::test_<area>_english_unchanged`).
- Keep the area's existing suites green.

- [ ] T015 [US1] Invoices, credits, refunds, payments and financial reversals:
  - `invoice_actions`, `credit_actions`, `payment_actions`, `financial_reversal_actions`;
  - the invoice, credit and payment paths in `core`.
- [ ] T016 [US1] Orders, commitments, customer holds and supply assignments:
  - `order_actions`, `commitment_actions`, `customer_hold_actions`;
  - `supply_assignment_actions`, `supply_assignments`;
  - the order and commitment paths in `core`.
- [ ] T017 [US1] Deliveries, shipments, receipts, returns and corrections:
  - `shipment_actions`, `shipments`;
  - `return_disposition_actions`, `return_dispositions`;
  - `movement_correction_actions`;
  - the movement paths in `core`, and the shipment compatibility error through `RefusalMixin`.
- [ ] T018 [US1] Opening stock and cost reviews:
  - `opening_stock_actions`, `opening_cost`;
  - `costing`, `inventory_costing`, `carrying_value`, `cost_review_draft`;
  - the domain costing refusals through `RefusalMixin`;
  - the Pydantic re-raises as `request_fields_invalid`.
- [ ] T019 [US1] [US2] Master data and the shared path:
  - `reference_workspace`, including the field-name `term` values;
  - `item_imports` (reachable sites);
  - `tenant_policy`, `delivery_actions`, `tools.application`, `artifacts`;
  - the remaining `scope: "286"` sites in `core`.
- [ ] T020 [FR-006] Confirm that no `scope: "286"` ratchet entry remains and that the
  localization contract is green.

## Phase 6: Browser proof (US1–US3)

- [ ] T021 [FR-005] Write `apps/web/scripts/service-refusals-browser.mjs`. It shows coded
  refusals, with fixture responses, in:
  - the invoice, order, master data and opening stock forms;
  - the chat panel.

  It covers de/nl/es at 390 and 1440 px, including one refusal with a `number` value and one
  with a `term` value, and the English fallback for an unknown code.

## Final Phase

- [ ] T900 `make spec-check`; add the new test files to `docs/SPEC_COVERAGE_MATRIX.md`.
- [ ] T901 Run Ruff on my own files only (`--no-cache`) and the complete backend suite (CI).
- [ ] T902 `make web-build`, i18n audit, node contracts, browser test.
- [ ] T903 `make docs-generate` (in case catalog-derived pages change).
- [ ] T904 [SC-001] Live: on an isolated stack, the German invoice form refuses gross 60.00 /
  net 50.00 / tax 9.50 with the German sentence, and the English account still sees the
  English one. Record the result in `quickstart.md`.
- [ ] T905 Write `docs/features/service-refusals.md`, covering:
  - the contract;
  - how to add a refusal;
  - how a later area empties its `later` entries.
- [ ] T906 Review the final diff against the Constitution and every FR and DR.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T004 | T005 | Pending |
| FR-002 | T004, T015–T019 | T005 | Pending |
| FR-003 | T008 | T009 | Pending |
| FR-004 | T010 | T011 | Pending |
| FR-005 | T012, T021 | T013 | Pending |
| FR-006 | T006, T014, T020 | T015–T019 | Pending |
| FR-007 | T006 | T007 | Pending |
| FR-008 | T010 | T011 | Pending |
| FR-009 | T012 | T013 | Pending |
| DR-001 | T006 | T015–T019 | Pending |
| DR-002 | T015–T019, T901 | — | Pending |
| DR-003 | T906 | — | Pending |
| DR-004 | T004 | T005 | Pending |
| SC-001 | T904 | — | Pending |
