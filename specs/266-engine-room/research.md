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

## Implementation decisions (2026-09-24)

- **I1 — Recorder module.** The recorder lives in `services/interaction_recorder.py`, not `telemetry/`. It calls services lazily, and `telemetry/` stays a leaf.
- **I2 — Retention without a new job type.** The job registry has no per-company system schedule that would run a purge for every company. The established rule is that the work which makes a history tidies it (`projections.refresh` forgets job runs, spec 181 FR-005). The recorder therefore deletes at most 500 expired rows of its company after a write, at most every 10 minutes per process and company. Reads already hide expired rows.
- **I3 — `write` kind.** A web request that commits events without a proposal (for example `POST /items`) was shown as "Read". It is now recorded as `write`. Found during the live browser check.
- **I4 — CLI boundary.** CLI commands call services directly as well as tools. The whole command is the boundary. It learns its company from the first tool call or event, and a command that touches no company records nothing.
- **I5 — Worker boundary.** The observation wraps the child's claim transaction in `jobs/runner.py`, so it ends after the commit that keeps the job's events.
- **I6 — MCP defaults.** The MCP server fills in every declared default, so only arguments whose value differs from the declared default count as used.
- **I7 — Test harness.** Recording through the test connection from the request thread and the recorder thread at once loses rows, and psycopg connections are not thread-safe. Web, catalog-wide and worker tests therefore run on a committed database with separate connections, as in production. Tests default to `REALITY_INTERACTIONS=off`; the engine-room tests switch it on.
- **I8 — Replay.** The time axis of `FlightRecorder.tsx` was not reused. Replay is a filtered window with step controls over the same list, which needed no second layout.

- **I9 — Recording off the response path.** The first measurement added about 6 ms (median) and 10 ms (p95) per web request: one session, INSERT and COMMIT per row, over Docker Desktop's network. Three changes followed:
  - **Background writer.** The serving processes (API lifespan, `build_remote_server`) start one writer thread, and web, MCP and chat rows are queued with a non-blocking put. CLI and worker children still write in line, because they exit right after.
  - **Batched writes.** The writer writes everything queued in one transaction, with one query per kind of link.
  - **Pure ASGI middleware.** The web boundary is now a pure ASGI middleware instead of `@app.middleware`, so the observation also covers a streamed body.

  Turning off `synchronous_commit` showed no gain and was dropped.

- **I10 — Owner review of the live view (2026-09-24).**
  - The model map stayed dark for most reads because no argument values were kept. Declared enum values are now kept as `summary.choices` and name their stage (FR-003, FR-008).
  - "Changed nothing" on every read hid the rows that did change something, so the lane is now empty for such reads.
  - Tool calls show a label (FR-016). Only 4 of 179 tools have a German catalog label, and the web dictionary translates 49 of the 172 English tool labels. The rest show English next to the technical name; translating them is follow-up work.
  - The owner's own page loads dominated the list, so they are hidden by default (FR-006).

- **I11 — Cockpit instead of a list (owner review, 2026-09-25).** The owner wants a control room: what happens now, a calm screen when nothing does, like an activity monitor. The Live tab therefore derives a one-minute cockpit in the browser from the rows it polls:
  - status line
  - channel meters with a 12 × 5 s trace
  - model stages with read and write counts
  - who is active now
  - a ticker of the last minute

  This is presentation of telemetry, not a business rule. Pause was dropped, because a view of "now" has nothing to hold. The register layout, aligned with the other Inspector registers, became the history view behind the Period chip, and the entry points about the past lead there. Page title and description moved into the page introduction (the ⓘ popover), where every other page keeps them; before that, the Live tab's popover showed the Timeline text.

- **I12 — One question, one place (owner review, 2026-09-25).** Two similar tables (interactions over a period, business events in Activities) confused the owner, although they count different things. The split is now by time:
  - **History** is the Activities tab, the business events: what changed, kept for good.
  - **Live** is the cockpit only: who accesses the model now, one minute, no filter bar and no table.

  A change marker in the ticker bridges the two. The interaction history view, the period and search controls, the pause, and the chat and "who changed this" entry points were removed from the UI. The API keeps its window read.

- **I13 — Curves (owner request, 2026-09-25).** The owner asked for Grafana-like curves of the most important things. There are four: load by channel, latency p50/p95, errors, and reads against changes, over 5/15/60 minutes.
  - **Data.** `GET /interactions/series` aggregates per step in SQL (`count … filter`, `percentile_cont`) over `(tenant_id, recorded_at)`. The browser does not load thousands of rows to count them itself, and a curve is complete the moment the tab opens.
  - **Drawing.** Plain SVG like the Home activity graph, because the app has no chart library and four line charts do not need one.
  - **Colour.** The five channels take the reference categorical order, validated with the dataviz palette validator against the app surfaces: every hard check passes in both modes. The light-mode contrast warning for three slots is relieved by the legend values and by the channel meters, which show each value as text.
  - **Errors** use the reserved critical status colour.

## Analysis (2026-09-24)

A consistency pass over `spec.md`, `plan.md`, `data-model.md`, `contracts/` and `tasks.md`, checked against the code on `origin/main`. No CRITICAL finding. Every HIGH finding is resolved in the artifacts.

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| A1 | HIGH | FR-002 listed kind `intake`, but the data model has no such kind, and no boundary observes intake on its own | Kind removed. Intake is recorded as its carrier (web, MCP, worker) and recognized by the Source stage its `source_record.*` events write (FR-001) |
| A2 | HIGH | US1 named channels Scheduler and Source intake, which the model and the clarification (no empty sweeps) exclude | US1 lists MCP, Chat, Web, CLI, Worker |
| A3 | HIGH | Draft FR-004 had business events carry the request correlation, but `business_event.correlation_id` already holds the proposal id | FR-004/DR-002 rewritten: interaction → committed event sequences (R3); no business column changes; T030 asserts it |
| A4 | HIGH | US4-3 "known read subject" needs argument values, which FR-003 forbids | Renamed "Who changed this"; limited to events |
| A5 | MEDIUM | The edge case removed interactions on archive, while the generic purge only runs on delete | Delete removes them; archive keeps them until they expire |
| A6 | HIGH | Recording before admission would store a refused foreign-tenant request in that foreign tenant | The middleware sits inside `protect_application_api` (T022); T017 proves no row in either tenant |
| A7 | MEDIUM | Owner-only (FR-013) did not say what applies to sandbox runs | The sandbox run owner counts as owner (edge case, T021) |
| A8 | MEDIUM | The plan omitted repository completeness gates: reporting-graph coverage exclusions, `data_model.yaml`, pinned isolation counts, migration test | T005, T011 |
| A9 | MEDIUM | Migration number may collide with the spec 265 branch | Resolved at rebase: 265 took `0094`/`0095`, this feature is `0096` |
| A10 | MEDIUM | DR-003 named "decision service" and "source intake" as recording points, unlike the plan's boundaries | DR-003 aligned: boundaries record; the tool layer and event emission annotate |
| A11 | LOW | The header pulse polls every 10 s, so the indicator can lag up to 10 s | Accepted; FR-005's 2 s applies to the Live tab |
| A12 | LOW | SC-001 is proven only by the manual quickstart | Accepted; quickstart steps 2–4 |
| A13 | LOW | Owner check under `REALITY_AUTH_MODE=disabled` was unspecified | Follows existing owner routes; T021 |

Coverage: all 15 FR and 4 DR appear in at least one test task and one implementation task (`tasks.md` Requirement Coverage). There are no orphan tasks: every task in phases 2–8 cites a requirement.
