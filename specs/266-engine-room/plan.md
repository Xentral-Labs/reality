# Implementation Plan: Engine Room

**Branch**: `266-engine-room` | **Date**: 2026-09-24 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Record one short-lived, value-free *interaction* whenever a request crosses into the application. That means a web tenant request, an MCP tool call, a chat tool call, a CLI command or a worker job run. Each interaction links to the business events it committed. Owners can watch them in a new Inspector tab, Activities → Live, which polls a cursor endpoint every second.

The design reuses the contextvar technique of the Storyline trace (spec 182), but uses its own table, its own session and no values. It needs one new table, no business-table change, no new infrastructure and no new dependency.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript (React/Vite) for the web
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React
**Storage**: PostgreSQL, one new table `interaction` ([data-model.md](data-model.md))
**Testing**: pytest (unit, service, business story, adapter, tenant isolation); web node tests and Playwright browser script
**Project Type**: backend services/API/CLI/MCP plus independent frontend
**Constraints**: UTC; opaque IDs; strict tenant scope; recording never fails or noticeably slows the observed call (≤ 5 ms p95)
**Scale/Scope**: every tenant; up to several interactions per second per company under continuous demo intake; 7-day retention

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Unchanged. An interaction only links to the business events it committed (R3). Source and document stages are reached through those events. | PASS |
| Reality owns operational state | Interactions hold no business state, and no business read may import them (architecture test, DR-001). | PASS |
| Proven schema only | Every typed column serves a spec filter, an order or a lifecycle (data-model table, "Why typed"). Values are not stored at all. No business table gains a column; `business_event.correlation_id` keeps its meaning. | PASS |
| Tenant + shared service boundaries | The table is tenant-keyed. Every read goes through `services/interactions.py` with a tenant predicate. Recording sits at the shared boundaries: middleware, MCP `invoke`, chat `_call_tool`, CLI callback, job handler and tool layer. No adapter writes through the ORM. The table is added to `tenant_isolation_catalog.yaml`. | PASS |
| Spec/test traceability | Every FR/DR maps to a test below. | PASS |
| Explainable web behavior | Every row links to its events, proposal and chat session through the existing Inspector. Model stages are computed in the service, not in the browser. | PASS |
| Received values not recomputed | Nothing is derived from business values. Duration and counts are properties of the interaction itself. | PASS |
| Smallest coherent design | Polling instead of SSE/NOTIFY (R4); a separate recorder instead of generalizing the storyline trace (R2); no MCP/CLI read tool (see Decisions). | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/
  db/core.py                          # + Interaction model
  ../../migrations/versions/<next>_engine_room_interaction.py   # migration (number per T004)
  services/interaction_recorder.py    # NEW: Observation contextvar, begin/end/observe, note_*(), record, tidy (research I1, I2)
  services/interactions.py            # NEW: list_interactions(), events_of(), pulse(), purge_expired(), stage map
  services/core.py                    # emit_business_event → note_event(event.id)
  tools/application.py                # wrap run_read_tool / create_change_proposal / approve / reject: note kind & proposal
  jobs/runner.py                      # observe(channel="worker") around the child's claim transaction (research I5)
  mcp/server.py                       # observe(channel="mcp") in _handler.invoke
  agent/mcp_chat.py                   # observe(channel="chat") in _call_tool
  cli/app.py                          # observe(channel="cli") in the command callback
  web/app.py                          # middleware observe(channel="web"); CORS allow_headers
  web/interactions_api.py             # NEW: GET /interactions, /interactions/{id}/events, /interactions/pulse
config/tenant_isolation_catalog.yaml, config/data_model.yaml   # register table
apps/web/src/
  api.ts                              # correlation + refresh headers; interactions client
  unified/inspectorSections.ts, routing.ts   # Activities → ["history", "live"]; filter params
  unified/EngineRoom.tsx              # NEW: Live tab (lanes, filters, pause, model map, replay)
  unified/engineRoomModel.ts          # NEW: pure merge/dedupe/grouping (node-testable)
  unified/Shell.tsx, HomePulse.tsx, MCPAccess.tsx, ChatPage.tsx/CompanyChatPage.tsx,
  Inspector.tsx, commandPaletteEntries.ts     # entry points (US4)
  localization.tsx                    # de/nl/es labels
docs/features/engine-room.md          # NEW durable contract; link from AGENTS.md is not needed
```

The dependency direction is `telemetry/interactions.py` (leaf, stdlib and contextvars only) ← services/tools/adapters. `services/interactions.py` depends on db and catalogs only.

## Design

### Reality flow

N/A for new business data. An interaction references committed `business_event` rows by tenant sequence, and optionally a proposal (`action`). Documents and source records are reached through those events' existing links.

### Recording flow

1. A boundary calls `with observe(tenant_id, channel, actor, operation, correlation_id):`. If an observation is already open, it becomes a nested no-op. The one exception is chat inside a web request: chat tool calls are their own boundary and inherit the outer correlation (US1-2).
2. The tool layer calls `note_kind("propose"|"decide")` and `note_proposal(id)`. `emit_business_event` calls `note_event(event.id)`. Without an observation all of these are free no-ops.
3. On exit, the outcome is derived from the result: `ok`; `refused` for `NotFound`/`InvalidOperation`/`PermissionError`/validation errors and HTTP 4xx; `failed` otherwise; `awaiting_decision` when a proposal was created and not executed. The error code comes from `mcp.server.ERROR_CODES` or the HTTP status.
4. `services.interactions.record()` opens its **own** `Session`. It keeps the noted event ids that exist, computes the ranges and inserts the row. It is wrapped so any exception is logged and counted (`reality_interaction_record_failures_total`, bounded labels) and never propagates (FR-012).
5. Web: the middleware records after `call_next` in the threadpool, like the storyline middleware. The engine-room routes are skipped.

### Read flow

`list_interactions(session, tenant_id, filters)` runs a tenant-predicated query. It joins the actor labels (user, token and issuer, revoked flag) and computes `stages` from the event subject types and the catalog `reads` of the operation (R6).

The subject filter looks up the subject's event sequences through the existing `business_event` indexes, then keeps interactions whose `[first, last]` range contains one of them and whose `event_ranges` confirm it.

### Web

- The Live tab polls `after=cursor` every 1 s while the page is visible and stops on `document.hidden` or pause, counting what arrived in the meantime (FR-014).
- `engineRoomModel.ts` merges pages, deduplicates by id and groups rows by `correlation_id`.
- Layout: three lanes per row (access · intent · reality), expandable per correlation. The model map is a static SVG of the stages with read (outline) and write (fill) marks; motion follows `prefers-reduced-motion`.
- Replay uses `from`/`to` and step controls. `FlightRecorder.tsx` is evaluated first for the time axis; it is reused only if it fits without reshaping.
- Correlation: `api.ts` keeps a module-level id, rotated on the capturing `pointerdown`/`keydown` listener and on route change. Timer-driven callers (HomePulse, ActivityGraph, work counts, inbox badge, readiness, the pulse itself) pass `refresh: true`.

### Data and migration impact

See [data-model.md](data-model.md). Migration `0096` (after spec 265's `0094`/`0095`) adds only the new table.

### Failure, security, and tenant behavior

- Owners only; everyone else gets `404` (FR-013), including a platform admin without membership.
- There are no values in rows (FR-003). `summary.arguments` is filtered to the property names of the tool's input schema, so an unexpected key cannot smuggle text in.
- Recording failure → log + metric, and the call proceeds (FR-012).
- A client-supplied correlation is validated. The refresh flag only lowers default visibility (R5).
- Playground/sandbox tenants are recorded like any company. The storyline trace keeps running independently.
- Rollback of a business transaction: its events are not linked (R3). The interaction is still recorded, as `failed`.

### Decisions

- **No MCP/CLI read tool for interactions in this feature.** The engine room observes channels, and an agent reading its own telemetry is not a stated need. It is a noted follow-up (`reality interactions tail`) in case operators ask for it.
- **One interaction per chat tool call, not per chat turn.** The turn is represented by the carrying web request row with the same correlation.

## Test Strategy and Traceability

Test files (new unless noted), under `packages/reality-core/tests/`:

- `test_engine_room_recording.py` (service/adapter)
- `test_engine_room_reads.py` (service/API)
- `test_engine_room_story.py` (business story)
- `test_engine_room_architecture.py` (unit)
- `tenant_isolation/` (catalog entry and family)

Web: `apps/web/scripts/engine-room-model.test.mjs` and `engine-room-browser.mjs`.

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001 | adapter | `test_engine_room_recording.py::test_each_channel_records_one_interaction` (web GET, web POST, MCP invoke, chat call, CLI command, worker job) | table/module missing |
| FR-001 | service | `::test_empty_scheduler_sweep_records_nothing` | positive control: job run records one |
| FR-002 | unit | `::test_operation_is_route_template_not_raw_path` | raw path stored |
| FR-003 | service | `::test_no_argument_or_result_values_across_catalog`: every read tool with sentinel strings; the sentinel never appears in any column | module missing |
| FR-004 | story | `test_engine_room_story.py::test_mcp_proposal_web_approval_is_one_trace` | no link |
| FR-004 | service | `::test_rolled_back_events_are_not_linked` | reused sequence linked |
| FR-005 | API | `test_engine_room_reads.py::test_after_cursor_returns_late_commits_once` | missing route |
| FR-006 | API | `::test_filters` (channel, actor, kind, outcome, correlation, subject) | missing route |
| FR-007 | API | `::test_events_of_interaction_are_timeline_rows` | missing route |
| FR-008 | unit | `::test_stages_from_events_and_catalog_reads`, `::test_unknown_operation_marks_no_stage` | missing |
| FR-009 | browser | `engine-room-browser.mjs` entry points (header, Home, palette, MCP token, chat, Inspector) | missing UI |
| FR-010 | adapter | `test_engine_room_recording.py::test_engine_room_routes_not_recorded`, `::test_refresh_header_hidden_by_default` | recorded / shown |
| FR-011 | service | `test_engine_room_recording.py::test_recording_tidies_expired_rows_of_its_company_at_most_every_interval`; `test_engine_room_reads.py::test_retention_hides_rows_older_than_seven_days`, `::test_purge_removes_only_expired_rows` | missing tidy |
| FR-012 | service | `::test_recorder_failure_does_not_fail_call` with a raising writer, plus a positive control that a normal write lands | exception propagates |
| FR-013 | API | `test_engine_room_reads.py::test_member_and_foreign_owner_get_404` | missing route |
| FR-014 | node | `engine-room-model.test.mjs` pause buffer and resume merge | missing module |
| FR-015 | API + browser | `::test_window_query_orders_by_cursor`; browser replay step | missing |
| DR-001 | unit | `test_engine_room_architecture.py`: only the allowlisted modules import `Interaction` | positive control: the allowlist is non-empty and the import is found |
| DR-002 | story | same as FR-004, plus assert `business_event` columns unchanged | — |
| DR-003 | isolation | `tenant_isolation` catalog entry and family for `interaction` | catalog count mismatch |
| DR-004 | adapter | `test_engine_room_recording.py::test_actor_attribution_per_channel` (user, token+issuer, job) | missing |
| SC-003 | measurement | quickstart step 5 (p95 overhead, quiet machine) | — |

Existing suites that must stay green: `test_storyline_trace.py`, `test_home_readiness.py`, `test_migrations.py`, `tenant_isolation`, `test_ai_mcp.py`, `make docs-catalog-check`, `npm run i18n:audit`, `make web-build`.

## Rollout and Rollback

- The migration is additive. Old code ignores the table.
- The recorder can be disabled by setting `REALITY_INTERACTIONS=off`. That is an operator switch for an incident, not a product setting. It skips recording entirely, and the Live tab then states that recording is off.
- Rollback: revert the code and downgrade `0096` (drops the table). No business data is affected.
- Observability: a record-failure counter and a record-duration histogram (bounded labels: channel, outcome).

## Review Risks

- **Overhead on hot paths.** One insert per request for every tenant. It is measured before merge (SC-003). If the budget is missed, fall back to buffered inserts per process (flush ≤ 250 ms), which still meets SC-002.
- **Volume under continuous demo intake.** Measure rows per day on a live-demo company. The index design assumes ≤ 1 M rows per tenant per 7 days.
- **Chat streaming thread.** `web/chat_stream.py` may run the turn outside the request context. The contextvar must be propagated (`copy_context`) or the correlation passed explicitly. Test US1-2 covers this.
- **Worker runs in a child process.** The observation must open inside the child, around `definition.handler` in `services/scheduled_jobs.py`, not in `execute_process`.
- **Double wrapping with the storyline recorder.** Order the wrappers so both see the same call. `test_storyline_trace.py` stays green.
- **Migration number collision** with the spec 265 branch (see Data).

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
