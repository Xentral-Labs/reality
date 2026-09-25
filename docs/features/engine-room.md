# Live monitor (engine room)

Authority: [spec 266](../../specs/266-engine-room/spec.md).

The live monitor (German "Live-Monitor", internally the engine room) shows company owners every interaction with their company's model as
it happens: who, through which channel, what was asked, and what it changed. It lives
under **Inspector → Activities → Live**. It is observation, never business authority.
What happened to the business stays in `business_event`. An interaction only records
that somebody asked for something, and which committed events came of it.

## What is recorded

One `interaction` row per crossing into the application:

| Channel | Boundary | Actor |
|---|---|---|
| web | `record_interactions` middleware in `web/app.py`, inside `protect_application_api` | the signed-in person |
| mcp | `_handler.invoke` in `mcp/server.py` | the MCP token, with its issuer |
| chat | `_call_tool` in `agent/mcp_chat.py` (inherits the carrying web request's correlation) | the person of that request |
| cli | the `boot` callback in `cli/app.py`; the company comes from the first tool call or event | the operator |
| worker | around the child's claim transaction in `jobs/runner.py` | the job run |

The tool layer (`run_read_tool`, `create_change_proposal`, approve and reject) and
`emit_business_event` only annotate the open interaction. Nested boundaries join the
outer one. The one exception is chat inside a web request.

Rows carry no argument or result values. They hold the operation name (tool name or route
template), the kind (`read`, `write`, `propose`, `decide`, `job`), the outcome and error
code, the duration, the declared argument names, a result count, and arguments whose value
is one of the tool's declared enum values (`family: party`). A closed-list choice is
vocabulary, not content, and it names the stage the model map marks as read. Links run from the
interaction to the committed event sequences it caused. Events of a rolled-back
transaction are not linked, and `business_event` gains no column.

Not recorded: requests refused at company admission, the engine room's own routes,
unauthenticated and account-level routes, empty scheduler sweeps and idle worker polls.
Timer-driven reads from the web (Home, work counts, journey refresh, demo status) send
`X-Reality-Refresh: 1`. They are stored with `refresh = true` and hidden by default.

## Reading it

`GET /api/tenants/{tenant_id}/interactions` supports these parameters:

- a cursor (`after`) or a window (`from`/`to`)
- filters `channel`, `kind`, `outcome`, `actor_user_id`, `mcp_token_id`, `correlation_id`, and `subject_type` plus `subject_id` ("who changed this")
- `include_refresh`
- `limit`

`/pulse` feeds the header indicator. `/{id}/events` lists the linked events. The routes
serve active owners only and return 404 to everyone else, platform admins included. Model
stages are derived at read time: written stages from the event subject types, read stages
from the resource catalog's `match`/`tables` membership. Web routes mark no read stage.

The browser polls every second while the tab is visible. Rows recorded in the last five
seconds are always returned again, so an insert that committed late from another process
still arrives. The client deduplicates by id.

## The Live tab is a cockpit

The Live tab shows the last minute only:
- a status: active with a count, or all quiet
- a meter per channel with its rate, a trace of twelve five-second buckets and its errors
- the model stages with their reads and writes
- who is active now
- a ticker of that minute

Nothing older appears there, so a quiet company looks quiet. The derivation is pure presentation (`cockpit()` in `apps/web/src/unified/engineRoomModel.ts`).

The history view is the register behind the Period chip (last hour, 24 hours, 7 days). It has search, filters, the model map and step controls. The entry points that ask about the past open it.

## Retention and operation

Interactions older than seven days are hidden from reads. The recorder deletes up to 500
of them per company after a write, at most every 10 minutes per process (the spec 181
FR-005 rule). Company deletion removes them through the generic tenant purge.

`REALITY_INTERACTIONS=off` switches recording off, as an operator switch for incidents.
A recorder failure never fails the observed call. It is logged and counted in
`reality.interactions.record_failures`. The time spent recording is measured in
`reality.interactions.record_duration`.

## Verification

- Backend:
  - `packages/reality-core/tests/test_engine_room_recording.py`
  - `test_engine_room_channels.py`
  - `test_engine_room_reads.py`
  - `test_engine_room_migration.py`
  - `test_engine_room_architecture.py`
- Web: `apps/web/scripts/engine-room-model.test.mjs`
- Live browser check against a real API: `apps/web/scripts/engine-room-live-browser.mjs` (see the spec quickstart).
