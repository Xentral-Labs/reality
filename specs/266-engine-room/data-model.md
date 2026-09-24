# Data Model: Engine Room

One new tenant-scoped table. No business table changes.

## `interaction`

Operational telemetry (DR-001). No business read, projection, exception rule or decision may query it. An architecture test enforces this (plan, DR-001).

| Column | Type | Why typed (Constitution III) |
|---|---|---|
| `tenant_id` | FK `tenant.id`, PK part | tenant scope |
| `id` | opaque string `int_…`, PK part | identity |
| `cursor` | bigint identity, unique | poll order and cursor (FR-005) |
| `started_at`, `recorded_at` | UTC | time axis, replay window (FR-015), retention (FR-011) |
| `duration_ms` | int | shown and filtered |
| `channel` | check: `web`, `mcp`, `chat`, `cli`, `worker` | filter (FR-006) |
| `kind` | check: `read`, `write`, `propose`, `decide`, `job` | filter, lane; `write` = committed events without a proposal |
| `operation` | string ≤ 200 | tool/command name or route template; never a raw path |
| `outcome` | check: `ok`, `refused`, `failed`, `awaiting_decision` | filter |
| `error_code` | string null | refused/failed reason code, no message text |
| `actor_user_id` | FK `app_user.id` null | filter by person |
| `mcp_token_id` | FK `(tenant_id, mcp_access_token.id)` null | filter by client (US4-1) |
| `job_id` | string null | worker run reference |
| `correlation_id` | string ≤ 64 | grouping (FR-004) |
| `proposal_id` | FK `(tenant_id, action.id)` null | trace to decision (US2) |
| `event_first_sequence`, `event_last_sequence` | bigint null | subject filter via range lookup (US4-3) |
| `event_ranges` | JSON `[[first,last],…]` null | exact committed events when not contiguous |
| `refresh` | bool | default-hidden background refresh (FR-010) |
| `summary` | JSON ≤ 1 KiB | argument **names** and result count only (FR-003) |

**Indexes**:
- `(tenant_id, cursor)`
- `(tenant_id, recorded_at)` for replay and retention
- `(tenant_id, correlation_id)`
- `(tenant_id, event_first_sequence, event_last_sequence)`
- plus FK indexes on `actor_user_id`, `mcp_token_id` and `proposal_id` (FK index gate)

**Check constraints**: the enumerations above, and `octet_length(summary::text) <= 1024`.

**Lifecycle**: append-only. Rows older than 7 days are hidden from reads and deleted in bounded batches by the recorder's tidy step (research I2). They are removed with the company by the existing generic tenant purge (`services/core.py` walks `Base.metadata.sorted_tables`). Account deletion nulls `actor_user_id` through its generic walk over every `app_user` reference. MCP tokens are revoked, never deleted, so `mcp_token_id` stays referenced and reads mark it revoked.

**Migration**: `0094_engine_room_interaction.py` creates the table. Downgrade drops it. There is no backfill: history before deployment never existed.
