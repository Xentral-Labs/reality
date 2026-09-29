# Tasks: Dunning Run and Escalation

**Input**: Design documents from `/specs/295-dunning-run/`

**Tests**: Written before their implementation task and observed failing where practical. Every "no finding" assertion has a positive control; every refusal asserts its code. Paths are relative to the repository root; `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the approved scope and the three clarifications in `specs/295-dunning-run/spec.md`
- [x] T002 Record design decisions R1–R7 in `specs/295-dunning-run/research.md`
- [x] T003 Define the three tables in `specs/295-dunning-run/data-model.md` and the tool contract in `specs/295-dunning-run/contracts/dunning-run.md`
- [x] T004 Complete the Constitution Check in `specs/295-dunning-run/plan.md`

## Phase 2: Foundational — Schema and Shared Readers

- [x] T005 [FR-007] [FR-004] [DR-001] Failing migration and model parity test for `dunning_schedule_level`, `collection_handover` and `collection_handover_invoice` (checks, uniques, FK indexes) in `core/tests/finance/test_dunning_runs.py`
- [x] T006 [DR-001] Add the models in `core/src/reality/db/core.py` and migration `core/migrations/versions/0102_dunning_run.py`
- [x] T007 [DR-001] Register the tables in `core/config/data_model.yaml`, the reporting-graph deferral in `core/tests/test_reporting_graph_coverage.py`, `core/tests/test_schema_indexes.py` and `core/config/tenant_isolation_catalog.yaml`
- [x] T008 [DR-003] Extract `_record_notice(..., source_key)` in `core/src/reality/services/dunning.py`; the spec 247 tests in `core/tests/finance/test_commercial_edges.py` stay green unchanged
- [x] T009 [FR-011] Add `collection` to `HOLD_REASONS` (with its Web label in four languages) and give `hold_party_delivery` the codebase's `_commit` flag in `core/src/reality/services/core.py`; existing hold tests stay green

## Phase 3: User Story 2 — Company dunning schedule (P1)

**Independent Test**: `pytest core/tests/finance/test_dunning_runs.py -k schedule`

- [x] T010 [P] [US2] [FR-007] Failing tests: set and read the schedule, change it, each coded refusal (`dunning_schedule_incomplete`, `dunning_schedule_value_invalid`, the existing `finance_account_default_missing`), stale revision (`dunning_preview_stale`), tenant isolation, in `core/tests/finance/test_dunning_runs.py`
- [x] T011 [US2] [FR-007] Implement `schedule` and `set_schedule` in `core/src/reality/services/dunning_runs.py` and the `finance.dunning.schedule.set` route in `core/src/reality/tools/finance.py`

## Phase 4: User Story 1 — Dunning run and escalation (P1)

**Independent Test**: `pytest core/tests/finance/test_dunning_runs.py -k "run or collection"`

- [x] T012 [P] [US1] [FR-001–FR-003] [FR-008] [FR-010] Failing preview tests: level 1 after the waiting days (and not one day earlier, as positive control), level 2 after a level 1 notice plus waiting days, reversed notice ignored, per-currency and per-level grouping, customer filter, credit available left out and named, schedule missing refused with its code, nothing recorded by the preview, in `core/tests/finance/test_dunning_runs.py`
- [x] T013 [US1] [FR-001–FR-003] [FR-010] [DR-002] Implement `invoice_dunning_state` and `run_context` in `core/src/reality/services/dunning_runs.py` with one read per source (statement-count test)
- [x] T014 [P] [US1] [FR-009] [DR-003] Failing confirmation tests: notices recorded as spec 247 notices with schedule fees; deselected item not dunned; item paid after preparation skipped as `paid`; second run on the same date skips as `level_changed`; zero fee without a fee charge; replay idempotent; all-or-nothing on a failure; a schedule changed since the review is stale (`dunning_preview_stale`), in `core/tests/finance/test_dunning_runs.py`
- [x] T015 [US1] [FR-009] Implement `confirm_run` and the `finance.dunning.run` route
- [x] T016 [P] [US1] [FR-004] [FR-011] Failing handover tests: level 3 required (`collection_level_missing`, with a level 3 positive control), open required, mixed customers, handed over twice, reason required; hold placed with reason `collection`; existing hold kept; later run proposes nothing for the item, in `core/tests/finance/test_dunning_runs.py`
- [x] T017 [US1] [FR-004] [FR-011] Implement `record_handover`, `handover_detail`, `handovers` and the `finance.dunning.collection.handover` route
- [x] T018 [US1] [FR-012] Name the last notice, derived level and handover in the invoice's document inspector (a "Dunning" section linking the notice and the handover's source)

## Phase 5: Surfaces

- [ ] T019 [P] [FR-005] [FR-012] Failing adapter tests (MCP reads and proposals, CLI, HTTP read endpoints, tenant isolation) in `core/tests/finance/test_dunning_run_adapters.py`
- [ ] T020 [FR-005] MCP tools in `core/src/reality/mcp/catalog.py`, CLI commands, HTTP endpoints in `core/src/reality/web/api.py`, sandbox read allowlist
- [ ] T021 [FR-005] Catalogs: `command_catalog.yaml`, `tool_catalog.json`, `action_discovery.json` and `apps/web/scripts/fixtures/action-reference.json`, `resource_catalog.yaml` (German labels), `service_refusals.json` and de/nl/es, `refusal_ratchet.json`, `business_event_catalog.yaml` and `catalogs._literal_business_events`, pinned counts
- [ ] T022 [FR-005] Web: schedule form, run review with deselection and skip reasons, handover action, hold reason label in four languages, in `apps/web/src/finance/`; i18n audit and contract tests

## Phase 6: Journey and Verification

- [ ] T023 [FR-006] [SC-001] [SC-003] N04 business story through reviewed tools (schedule, three customers at three levels, payment between runs, handover and hold) in `core/tests/scenarios/test_catalog_finance.py`
- [ ] T024 [FR-006] [SC-002] Promote N04 to `supported` in `core/config/business_journey_catalog.yaml` with evidence, tools and specific keywords; check the Guide question does not steal neighbour journeys; regenerate the product advisor knowledge
- [ ] T025 `make docs-generate`, `make docs-catalog-check`, `make spec-check lint`, the full backend suite and the Web checks
- [ ] T026 Manual Web check per `quickstart.md` on an isolated stack
- [ ] T027 Review of the diff; fix findings; update `docs/scenarios/roadmap.md`
