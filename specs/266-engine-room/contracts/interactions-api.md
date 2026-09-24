# Contract: Interactions API

All routes are under `/api/tenants/{tenant_id}` and restricted to active company owners. Anyone else, including platform admins without membership, gets `404`. These routes are never recorded themselves.

## `GET /interactions`

Query parameters (all optional):

| Parameter | Meaning |
|---|---|
| `after` | cursor; rows with a greater cursor plus rows recorded in the last 5 s |
| `from`, `to` | UTC window for replay (FR-015); mutually exclusive with `after` |
| `channel`, `kind`, `outcome` | repeatable enumerations |
| `actor_user_id`, `mcp_token_id`, `correlation_id` | exact filters |
| `subject_type` + `subject_id` | interactions whose linked events concern that subject |
| `include_refresh` | `true` shows background refresh (default `false`) |
| `limit` | 1–500, default 200 |

Response:

```json
{
  "interactions": [
    {
      "id": "int_…", "cursor": 1842, "started_at": "…Z", "recorded_at": "…Z",
      "duration_ms": 38, "channel": "mcp", "kind": "read",
      "operation": "inventory.read", "outcome": "ok", "error_code": null,
      "actor": {"kind": "mcp_token", "id": "mcpt_…", "label": "Claude Desktop",
                "issuer": {"id": "usr_…", "label": "Anna"}, "revoked": false},
      "correlation_id": "c_…", "proposal": null,
      "events": {"count": 0, "first_sequence": null, "last_sequence": null},
      "stages": {"read": ["reservation", "movement"], "written": []},
      "summary": {"arguments": ["item_id", "location_id"], "result_count": 120},
      "refresh": false
    }
  ],
  "cursor": 1842,
  "retention_starts_at": "…Z",
  "truncated": false
}
```

`stages` is computed at read time (R6). `truncated: true` means more rows exist than `limit`. The client then states that it shows the newest `limit` rows.

## `GET /interactions/{interaction_id}/events`

Returns the committed business events linked to one interaction, in sequence order, as `TimelineEvent` rows (same shape as the existing timeline). Each opens the existing event Inspector.

## `GET /interactions/pulse`

`{"latest_cursor": 1842, "latest_at": "…Z"}`. The shell header indicator reads it every 10 s (owners only).

## Request headers accepted from the web client

- `X-Reality-Correlation`: 1–64 characters `[A-Za-z0-9_-]`. Anything else is replaced by a server-generated id.
- `X-Reality-Refresh: 1`: marks a timer-driven request (R5).

Both are added to the CORS `allow_headers`.
