---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Engine Room

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/interactions-api.md` and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Paths are relative to the repository root; `core/` abbreviates
`packages/reality-core/` and `web/` abbreviates `apps/web/`.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement appears in at least one test task and one implementation
or documentation task. Test tasks precede the code they prove and are observed failing first.
Every negative test is paired with a positive control, so it cannot pass only because the
code under test does not exist yet.

**Honest note on order**: the recorder core (T010–T015) was written before its tests in
this session; the web model (T026) was observed failing first. The negative tests all
carry positive controls.

## Phase 1: Specification and Design Gates

- [X] T001 Confirm owner approval of scope, placement (Activities → Live plus entry points) and the three clarifications (7 days, owners only, job runs with effect), and absence of clarification markers, in `specs/266-engine-room/spec.md`
- [X] T002 Confirm every Constitution Check row is PASS and the one-table schema is justified column by column in `specs/266-engine-room/plan.md` and `data-model.md`
- [X] T003 Run the analysis pass and resolve every CRITICAL or HIGH finding across `specs/266-engine-room/` (findings A1–A12 in `research.md`)
- [X] T004 Before the first migration commit, re-derive the next free migration number against `origin/main` and every open branch that adds a revision (spec 265 carries a `0093`), and record it in `plan.md` — `0094_engine_room_interaction`; no remote branch carries 0094+; the local spec 265 branch has its own `0093` and renumbers when it rebases.

## Phase 2: Foundational — Table, Recorder, Event Link

**Goal**: One interaction row per boundary crossing, with committed events linked, and without breaking any call it observes.

### Tests

- [X] T005 [P] [DR-003] Add a failing upgrade/downgrade test for the `interaction` migration: columns, check constraints, identity `cursor`, the four indexes and the FK indexes, and drop on downgrade, in `core/tests/test_migrations.py` (extend next to the storyline table assertions) — written as `core/tests/test_engine_room_migration.py` rather than inside `test_migrations.py`.
- [X] T006 [P] [FR-002] [FR-003] Add failing unit tests for `telemetry/interactions.py`: nested `observe` is a no-op except chat inside web; `note_*` without an open observation is a no-op; `summary.arguments` is filtered to schema property names and capped at 1 KiB, in `core/tests/test_engine_room_recording.py`
- [X] T007 [P] [FR-004] Add failing service tests: events emitted inside an observation are linked by committed sequence; events of a rolled-back transaction are not linked even when their sequence is reused by a later transaction (positive control: the committed one is linked); non-contiguous events produce exact `event_ranges`, in `core/tests/test_engine_room_recording.py`
- [X] T008 [P] [FR-012] Add a failing test where the writer raises: the observed call returns its normal result, the failure counter increments, and the caller's session is neither committed nor rolled back by the recorder. Positive control: a normal write lands, in `core/tests/test_engine_room_recording.py`
- [X] T009 [P] [DR-001] Add an architecture test: only `telemetry/interactions.py`, `services/interactions.py`, `web/interactions_api.py`, the retention handler and the migration import `Interaction`. Positive control: the scan finds those modules, in `core/tests/test_engine_room_architecture.py`

### Implementation

- [X] T010 [DR-001] [DR-003] Add the `Interaction` model per `data-model.md` in `core/src/reality/db/core.py`, and the migration in `core/migrations/versions/<next>_engine_room_interaction.py`
- [X] T011 [DR-003] Register `interaction` in `core/config/tenant_isolation_catalog.yaml`, `core/config/data_model.yaml` (operational group next to `storyline_trace_entry`) and the excluded-table list in `core/tests/test_reporting_graph_coverage.py`, and bump any pinned table counts in the isolation suite
- [X] T012 [DR-001] [FR-002] [FR-003] [FR-012] Implement `Observation`, `observe()`, `note_kind()`, `note_proposal()`, `note_event()` and `note_result_count()` in `core/src/reality/telemetry/interactions.py` (stdlib and contextvars only), plus the `REALITY_INTERACTIONS=off` switch — implemented in `core/src/reality/services/interaction_recorder.py` (research I1), not `telemetry/`.
- [X] T013 [DR-002] [FR-004] [FR-012] Implement `record()` in `core/src/reality/services/interactions.py`: own `Session`, verify noted event ids after commit, compute first/last/ranges, insert, and swallow and count failures. Add the failure counter and duration histogram in `core/src/reality/telemetry/metrics.py`
- [X] T014 [DR-002] [FR-004] Call `note_event(event.id)` from `emit_business_event` in `core/src/reality/services/core.py`
- [X] T015 [FR-002] Wrap `run_read_tool`, `create_change_proposal`, `approve_and_execute_proposal` and `reject_proposal` to note kind, proposal and result count, stacked with the storyline wrappers, in `core/src/reality/tools/application.py`. `core/tests/test_storyline_trace.py` must stay green

## Phase 3: User Story 1 — Watch interactions live (P1)

**Independent test**: quickstart step 2, plus MCP and chat reads appear with channel and actor.

### Tests

- [X] T016 [P] [US1] [FR-001] [DR-004] Add failing adapter tests, one per channel, each asserting exactly one row with channel, actor, operation, kind, outcome and duration, in `core/tests/test_engine_room_recording.py`:
  - web GET under `request.state.user`
  - web POST that creates a proposal (`kind=propose`, `awaiting_decision`)
  - MCP `invoke`: token id; issuer from `mcp_access_token.created_by_user_id`
  - chat `_call_tool`: inherits the carrying request's correlation
  - CLI command
  - worker job inside the runner child: job kind and id
- [X] T017 [P] [US1] [FR-001] Add tests: an empty scheduler sweep and an idle worker poll record nothing (positive control: a job run records one); a request refused at company admission records nothing in either tenant; a member's refused tool call records `refused` with the error code and no values, in `core/tests/test_engine_room_recording.py`
- [X] T018 [P] [US1] [FR-002] Add a test that web `operation` is the route template (`/items/{item_id}`), never the raw path or query, in `core/tests/test_engine_room_recording.py`
- [X] T019 [P] [US1] [FR-003] Add a catalog-wide test: every read tool in the MCP registry is invoked with sentinel string values for its string arguments, and no sentinel appears in any column of any recorded row, in `core/tests/test_engine_room_recording.py`
- [X] T020 [P] [US1] [FR-010] Add tests: the engine-room routes are never recorded; `X-Reality-Refresh: 1` rows are stored with `refresh=true` and excluded unless `include_refresh=true` (positive control: they exist in the table), in `core/tests/test_engine_room_recording.py`
- [X] T021 [P] [US1] [FR-005] [FR-006] [FR-013] Add failing API tests in `core/tests/test_engine_room_reads.py`:
  - `after` returns a row that committed late with a lower cursor exactly once across two polls
  - each filter of the contract
  - `limit` sets `truncated`
  - a member, a foreign owner and a platform admin without membership get 404
  - a sandbox run owner gets 200
  - auth-disabled development mode follows the existing owner-route behavior

### Implementation

- [X] T022 [US1] [FR-001] [FR-010] Add the web middleware (registered inside `protect_application_api` so that admission runs first) with correlation and refresh header parsing, and add both headers to CORS `allow_headers`, in `core/src/reality/web/app.py`
- [X] T023 [US1] [FR-001] [DR-004] Open observations in `core/src/reality/mcp/server.py` (`_handler.invoke`), `core/src/reality/agent/mcp_chat.py` (`_call_tool`), `core/src/reality/cli/app.py` (command callback) and `core/src/reality/services/scheduled_jobs.py` (around `definition.handler`) — the worker boundary sits in `core/src/reality/jobs/runner.py` around the claim transaction (research I5); the CLI boundary is the `boot` callback (research I4).
- [X] T024 [US1] [FR-001] Propagate the observation context into the chat streaming path (`copy_context` or an explicit correlation) in `core/src/reality/web/chat_stream.py` / `core/src/reality/agent/streaming.py` — no change needed: `asyncio.to_thread` copies the request context, proven by `test_a_streamed_chat_turn_keeps_the_request_correlation_after_it_closed`.
- [X] T025 [US1] [FR-005] [FR-006] [FR-013] Implement `list_interactions()` and `pulse()` in `core/src/reality/services/interactions.py`, and the routes `GET /interactions` and `GET /interactions/pulse` with owner-or-404 in `core/src/reality/web/interactions_api.py`, included in `core/src/reality/web/app.py`
- [X] T026 [P] [US1] [FR-005] [FR-014] Add failing node tests for page merge, dedupe by id, cursor advance, pause buffer count and resume merge in `web/scripts/engine-room-model.test.mjs`
- [X] T027 [US1] [FR-005] [FR-014] Implement `web/src/unified/engineRoomModel.ts`; add `interactions()`/`interactionsPulse()` and the correlation and refresh headers in `web/src/api.ts`; mark timer-driven callers (`HomePulse.tsx`, `ActivityGraph.tsx`, `workCounts.ts`, inbox badge, readiness) as refresh
- [X] T028 [US1] [FR-005] [FR-006] [FR-014] Implement `web/src/unified/EngineRoom.tsx`: three lanes, filters bound to the URL, pause/resume with a counter, hidden-tab stop, truncated notice. Add the `live` tab in `web/src/unified/inspectorSections.ts` and `web/src/unified/routing.ts`, render it from `RealityInspectorPage.tsx`, and show it to owners only
- [X] T029 [US1] Add labels in `web/src/localization.tsx` (de/nl/es; German ERP vocabulary, "Motorraum"/"Live"), and run `npm run i18n:audit`

## Phase 4: User Story 2 — Follow a cause to its effect (P1)

### Tests

- [X] T030 [P] [US2] [FR-004] [FR-007] [DR-002] Add a business story: MCP proposes, a web owner approves, and the Live read shows request → decision → events connected by proposal id, with `events_of` returning timeline rows. Assert that `business_event` columns and `correlation_id` values are unchanged against a run with recording off, in `core/tests/test_engine_room_story.py` — covered by `test_engine_room_channels.py::test_web_approval_is_a_decision_linked_to_its_proposal` and the recorder tests; no separate story file.
- [X] T031 [P] [US2] [FR-004] Add stories: one web click with several requests shares one correlation; a worker demo-intake job links its `source_record.*` and document events, in `core/tests/test_engine_room_story.py` — one click → one correlation is `test_engine_room_recording.py::test_a_chat_call_inside_a_web_request_is_its_own_row_sharing_correlation`; worker events via `test_a_worker_run_is_one_interaction_and_empty_sweeps_are_none`.

### Implementation

- [X] T032 [US2] [FR-007] Implement `events_of()` and `GET /interactions/{id}/events` in `core/src/reality/services/interactions.py` and `core/src/reality/web/interactions_api.py`
- [X] T033 [US2] [FR-004] [FR-007] Rotate the correlation on capturing `pointerdown`/`keydown` and on route change in `web/src/api.ts`. In `EngineRoom.tsx`, group rows by correlation, show the proposal status path and link events, proposal and chat session to the existing Inspector, with "produced nothing" when empty

## Phase 5: User Story 3 — Model map (P2)

- [X] T034 [P] [US3] [FR-008] Add unit tests: written stages come from event subject types, read stages from catalog `reads` of the operation, an unknown operation or web route marks nothing, and `generic_tables` are ignored, in `core/tests/test_engine_room_reads.py`
- [X] T035 [US3] [FR-008] Implement the table-to-stage map and `stages` in `list_interactions()` in `core/src/reality/services/interactions.py`
- [X] T036 [US3] [FR-008] Render the model map (static SVG, outline = read, fill = written, `prefers-reduced-motion`) in `web/src/unified/EngineRoom.tsx`

## Phase 6: User Story 4 — Entry points (P2)

- [X] T037 [P] [US4] [FR-006] [FR-009] Add a failing browser script covering the header pulse, Home link, palette entry, MCP token "Calls of this client", chat "Show in engine room", Inspector "Who changed this", and a reloaded or shared filter URL, in `web/scripts/engine-room-browser.mjs` — delivered as the live script `web/scripts/engine-room-live-browser.mjs` against a real API (24/24 on 2026-09-24); chat and Home entry points are verified by build and contract tests, not by that script.
- [X] T038 [US4] [FR-009] Implement the entry points in `web/src/unified/Shell.tsx`, `HomePulse.tsx`, `commandPaletteEntries.ts`, `MCPAccess.tsx`, `ChatPage.tsx`/`CompanyChatPage.tsx` and `Inspector.tsx`, with the subject filter wired to `subject_type`/`subject_id`

## Phase 7: User Story 5 — Replay (P3)

- [X] T039 [P] [US5] [FR-015] Add API tests: a `from`/`to` window is ordered by cursor, and a window before retention returns `retention_starts_at` with an empty list, in `core/tests/test_engine_room_reads.py`
- [X] T040 [US5] [FR-015] Evaluate `web/src/unified/FlightRecorder.tsx` for the time axis and record the decision in `research.md`. Implement the replay mode with step controls and the beyond-retention notice in `EngineRoom.tsx`, and extend `engine-room-browser.mjs` — FlightRecorder not reused (research I8).

## Phase 8: Retention

- [X] T041 [P] [FR-011] Add a failing job test: rows older than 7 days are deleted in batches, newer rows and all business events stay, and the job is idempotent, in `core/tests/test_engine_room_recording.py` — replaced by tidy-on-write (research I2): `test_recording_tidies_expired_rows_of_its_company_at_most_every_interval`, `test_purge_removes_only_expired_rows`.
- [X] T042 [FR-011] Implement the `interactions.retention` handler in `core/src/reality/jobs/handlers/interactions.py`, register it in `core/src/reality/jobs/registry.py`, and add it to the job list in `docs/features/scheduled-jobs.md` — no new job type (research I2); `docs/features/scheduled-jobs.md` unchanged.

## Final Phase: Cross-Cutting Review

- [X] T900 Run the spec/traceability audit (`make spec-check`) and confirm the Requirement Coverage table below
- [ ] T901 Run Ruff from `core/` with `--no-cache` and the complete backend PostgreSQL suite in file order (as CI does), including `test_storyline_trace.py`, `test_home_readiness.py`, `test_ai_mcp.py` and `tenant_isolation`
- [X] T902 Run `make web-build`, `npm run i18n:audit`, `engine-room-model.test.mjs`, `engine-room-browser.mjs` and `home-live-browser.mjs`
- [X] T903 Review the migration chain against `origin/main` at merge time (T004) and the rollback (downgrade drops only `interaction`)
- [ ] T904 Measure SC-002 and SC-003 per `quickstart.md` step 5 on a quiet machine, back to back, and record the numbers in `quickstart.md`
- [X] T905 Write `docs/features/engine-room.md` (contract, noise rules, retention, operator switch), link it from `docs/WEB_SPEC.md`, and run `make docs-catalog-check`
- [ ] T906 Review the final diff against the Constitution and every FR/DR. Update `docs/V0_CHECKLIST.md` only after all checks are green

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T016, T017 | T022, T023, T024 | Done |
| FR-002 | T006, T018 | T012, T015 | Done |
| FR-003 | T006, T019 | T012 | Done |
| FR-004 | T007, T030, T031 | T013, T014, T033 | Done |
| FR-005 | T021, T026 | T025, T027, T028 | Done |
| FR-006 | T021, T037 | T025, T028, T038 | Done |
| FR-007 | T030 | T032, T033 | Done |
| FR-008 | T034 | T035, T036 | Done |
| FR-009 | T037 | T038 | Done |
| FR-010 | T020 | T022, T027 | Done |
| FR-011 | T041 | T042 | Done |
| FR-012 | T008 | T012, T013 | Done |
| FR-013 | T021 | T025, T028 | Done |
| FR-014 | T026 | T027, T028 | Done |
| FR-015 | T039 | T040 | Done |
| DR-001 | T009 | T010, T012 | Done |
| DR-002 | T030 | T013, T014 | Done |
| DR-003 | T005, T021 | T010, T011, T025 | Done |
| DR-004 | T016 | T023 | Done |
| SC-002, SC-003 | T904 | T013, T027 | Pending measurement |
