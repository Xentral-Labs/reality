# Demo Data Integration Interfaces

Status: implemented and verified locally on 2026-09-09. One shared service `services/demo_data.py` backs both active App and owned pending Playground adapters.

## Routes and authority

Active App: `/api/tenants/{tenant_id}/demo-data/...`. Pending private Playground: `/api/playground/runs/{run_id}/demo-data/...`, resolving the tenant server-side from current verified private ownership. Match the repository's existing tenant-prefix router convention at implementation; do not expose a pending wildcard bypass or arbitrary tenant override.

| Operation | Request / result |
|---|---|
| GET `preview` | Read-only exact compatible references or minimal prerequisites to add; ordinary/execution/incompatible populated Sandbox denied |
| POST `connect` | Preview fingerprint, request key, explicit confirmation; reuse/create only previewed master data; connection stopped |
| GET `imports/{id}` | Current owner read of the connection-bound immutable source, safe import status/outcomes and actual document reference |
| GET status | Connection identity/revision, intended and derived state, configured rate, run/profile/seed metadata, generated/pending/imported/failed, last import, next arrival, bounded result page |
| POST `control` | `{action, expected_revision, request_key, confirmed:true, rate?}` where action is start/pause/resume/stop/disconnect/reconnect/set_rate |
| POST `imports/{id}/retry` | Current owner confirmation, source/connection-bound ImportJob, same immutable payload and identity; never schedules a replacement source order |

Only rates 10, 60, 300 are valid; default 60, evenly spaced wall-clock intervals 360/60/12 seconds. Changes begin after a future interval. Same control key/input replays; changed input or stale revision conflicts. Lost control response is resolved by status/request identity, never guessing success. Manual connecting does not start intake. Explicit live-company creation calls connect and start in a caller-owned atomic transaction, with its completion marker; no separate browser requests are required. Stop/reconnect require a new explicit Start; Start after Stop creates a new continuous schedule ID. Resume keeps the same ID and no paused-period deliveries.

Source activity never reserves, fulfills, ships or replenishes. Since feature 168 a second schedule, `demo.settle_orders`, issues the invoice each order's plan states and records its customer payments under a separate settlement authority that may post the stated invoice, record money and allocate only an unambiguously stated reference (see [spec 168](../../168-demo-order-to-cash/spec.md)). Profile initialization, order intake and settlement use separate narrow authorization scopes; current actor, source, company and exact references are checked on every delivery. Archive/disconnect/revocation stops future intake. The execution fixture is always ineligible.

## Normal source processing

Source key `demo_data`, types `order`, `invoice` and `payment`; catalog metadata says synthetic and contains no credentials/provider claims. Registered interpreter consumes the exact lossless payload and calls shared evidence/commitment helpers under caller-owned transaction. One delivery carries a Poisson-distributed number of order payloads, at most six, following `integrations.demo_data.HOURLY_DEMAND` (`integrations.demo_data.plan`); the first keeps external ID `<schedule>:<delivery>`, later ones append `:<position>` and suffix their order number. Each payload includes schema/profile version, seed-derived product/customer choices (customers drawn from the referenced pool, weighted toward the first entries), continuous schedule ID, logical delivery ID, readable order number, business timestamp frozen at durable delivery creation (not an old missed due time), currency/unit and source-stated line/document values.

External identity is stable per schedule+logical delivery. Reuse stored payload on retry; never generate a new timestamp to disguise replay as an upstream update. Categories and unsupported promotional/cost metadata stay source/manifest content. Treat source-generated numbers as authored synthetic inputs, not claims of upstream/provider data.

One order occurrence creates one SourceRecord/ImportJob per order in its delivery burst and attempts interpretation; one settlement occurrence creates at most 25 invoice or payment SourceRecords/ImportJobs, oldest due first, with identities `{order external id}:invoice` and `{order external id}:payment:{n}`. Expected interpretation failure rolls back business effects to a savepoint, retains intake and a safe failure outcome. Unexpected transaction failure rolls back source plus scheduler completion and retries same delivery identity. Existing committing public intake APIs retain their historical behavior by wrapping the shared bound cores.

## Progress and bounds

Count distinct source orders from this connection's retained schedules, not raw events/versions or unrelated company imports. Imported requires the normal interpreted outcome and resulting document reference. Pending/failed reflect actual intake status; show terminal/unresolved scheduler errors separately where no source was committed. Last success is latest successful interpretation time; next arrival comes from enabled future schedule. Counts are observations, never new persisted business authority.

Page size 25, maximum 100, cursor bound to tenant/connection/filter and stable order. Links reach SourceRecord, ImportJob, interpretation outcome and actual order via existing inspectors. Saturation at 20 pending/failed source imports pauses generation visibly without advancing into catch-up bursts; explicit retry/recovery and resume are required. UI distinguishes running, paused, stopped, disconnected, throttled and error. Browser closure does not stop either deployed process.

## Proposed spec 147 cancellation extension

`cancel_queued_run(session, tenant_id, actor_id, schedule_id, expected_revision, request_key)` pauses timing and cancels only pending/retry work after scoped schedule/run locking. Retain cancelled run and request audit. Running/unknown work cannot be falsely cancelled; wait for bounded in-flight completion or return retryable conflict. Normal generic pause still preserves retry work. Demo controls alone use this explicit cancellation so their future-only resume meets spec 146. This approved extension is implemented in the shared scheduler service.

FR-026–028: the shell labels Sandbox beside the company name. Reports and contributor reads accept authorized practice tenants without changing mutation or admission policy. Demo Data presents state-aware primary controls and a latest-25 activity widget; five-second visible-page refresh only reads data. Recent snapshots use `imports?recent=true`, ordered by persisted import `created_at DESC, id DESC`; `has_more` labels truncation and no cursor is returned. Default history cursor behavior is preserved. Entries expose actual creation/completion times and held document numbers; next arrival is a scheduled time, not a guaranteed execution. Failed refresh retains existing data with a stale warning, and polling preserves input/confirmation state.

FR-029 moves the controls/live widget to `/app/demo-data?tenant=…`, reached by Demo Data immediately below Companies in the Company group for demo-profile companies or those with a Demo Data connection state. Integrations no longer embeds this panel. The dedicated route preserves service eligibility and tenant scope. This supersedes earlier descriptions placing the widget inside Integrations.
