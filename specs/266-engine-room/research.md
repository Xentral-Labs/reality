# Research: Engine Room

Measured on `origin/main` at 781f3e1d (2026-09-24).

## R1 — Where the model is entered

| Channel | Boundary on main | Covered by tool-layer hook? |
|---|---|---|
| MCP | `mcp/server.py` `_handler.invoke` → `mcp.catalog.dispatch_tool` | yes |
| Chat | `agent/mcp_chat.py` `_call_tool` → `dispatch_tool` | yes |
| CLI | `cli/app.py` → `tools.application` (44 call sites) | yes |
| Web | `web/api.py` tenant router `/api/tenants/{tenant_id}`: 192 routes, 22 via `run_read_tool` | **no** — most call services directly |
| Worker | `services/scheduled_jobs.py:748` `definition.handler(session, context, parsed)` inside the runner child process | no |
| Source intake | reached through one of the above (web upload, MCP tool, worker demo job) | via its carrier |

**Decision**: open one *observation* at each outer boundary (HTTP middleware for tenant routes, MCP `invoke`, chat `_call_tool`, CLI command callback, job handler call). The tool layer (`run_read_tool`, `create_change_proposal`, `approve_and_execute_proposal`, `reject_proposal`) only annotates the open observation (kind, proposal id), and opens one itself only when none is open.

**Rejected**: instrumenting only the tool layer (misses ~88 % of web routes); per-route decorators (192 edit sites and every new route forgets one).

## R2 — Precedent: the Storyline trace (spec 182)

`storyline/recorder.py` already wraps the same four tool functions (`tools/application.py:3393–3398`), wraps chat replies (`services/core.py:6829`) and records GET views from an HTTP middleware (`web/app.py` `record_storyline_views`). It differs in three ways that rule out reusing its table:

1. It stores argument and result values, because a storyline is exported and replayed as a lesson. FR-003 forbids values.
2. It exists only for tenants with an active storyline run.
3. It writes inside the caller's session and commits it (`_finish`). An engine-room write must survive a rolled-back business transaction and must never commit the caller's work.

**Decision**: a separate recorder, stacked beside the storyline wrappers and using the same contextvar technique. The storyline recorder stays unchanged. Merging the two is a possible follow-up once both are stable, not part of this feature.

## R3 — Linking to business events

`business_event.correlation_id` is already written as the proposal id (`services/core.py`, `shipments.py`, `credit_actions.py`; read in `customer_hold_actions.py:207`). Reusing it for a request correlation would change the meaning of a business column.

`emit_business_event` locks the tenant row `FOR UPDATE` before allocating `sequence`, so events of one transaction are contiguous per tenant. A rolled-back sequence can be reused by the next transaction.

**Decision**: `emit_business_event` appends the new event id to the open observation (a no-op without one). At finish, the recorder keeps only ids that exist after commit (one indexed query) and stores their sequences as `event_first_sequence`, `event_last_sequence` and the exact contiguous `event_ranges`. No business table gains a column.

## R4 — Live delivery

**Decision**: client polling with a cursor. `GET …/interactions?after=<cursor>` is polled every second while the tab is visible and paused while hidden. The server also returns rows recorded in the last 5 seconds, to cover inserts from other processes that commit out of cursor order. The client deduplicates by id. This gives ≤ 2 s at p95 (SC-002).

**Rejected**: SSE with PostgreSQL `LISTEN/NOTIFY`. It needs a dedicated connection per viewer or a fan-out process, an async listener in a synchronous SQLAlchemy stack, and proxy buffering control on Railway. That is new infrastructure for a view a handful of owners open (Constitution VII). Home already polls on a shorter-lived schedule (spec 149). If measurement ever shows polling load matters, SSE can replace the transport without changing the table or the contract.

## R5 — Noise

Home polls activity and readiness every 10 s, the inbox badge and tab work counts poll too. Without a marker, an idle open browser would dominate the view.

**Decision**: the web client sends `X-Reality-Refresh: 1` on timer-driven requests. They are recorded with `refresh = true` and hidden unless the viewer enables "Show background refresh". The engine-room routes themselves are never recorded (FR-010). The header only lowers a row's default visibility and never suppresses a record, so a client cannot hide from an owner.

## R6 — Model stages

`config/command_catalog.yaml` and `config/projection_catalog.yaml` declare `reads`/`writes` tables per entry. `resource_catalog.yaml` ignores `generic_tables`.

**Decision**: written stages come from the linked events' `subject_type`, and read stages from the catalog `reads` of a tool operation. Both are mapped by one table-to-stage map in the service and computed at read time. Web route templates have no catalog entry, so they mark no read stage (US3-2). Nothing is stored.

## R7 — Actor

- Web: `request.state.user.id`.
- MCP: the token id behind `SETTLING_TOKEN` (spec 263), and the person once spec 265's principal is on main.
- Chat: the web user of the carrying request.
- CLI: the operator principal the CLI already uses.
- Worker: job kind and scheduled job id.

Nothing is inferred (DR-004).

## R8 — Cost

The storyline middleware already performs one threadpool write per GET, for storyline tenants only. The engine room adds one small insert per boundary for every tenant. The budget is ≤ 5 ms at p95 (SC-003), measured in quickstart step 5. The write runs after the response body is produced (middleware) and in its own session.
