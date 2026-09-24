# Data Model: Decision Trail

Migration `0093_decision_trail` — additive, nullable, no backfill, reversible.

## `mcp_access_token`

| Column | Type | Null | Notes |
|---|---|---|---|
| `created_by_user_id` | `String`, FK `app_user.id`, indexed | yes | Owner who issued the token. `NULL` for tokens issued before this feature or outside the signed-in web path. |

Proof of use (Constitution III): joined to name the issuer on every MCP-settled
decision (spec FR-004), and filtered by tenant to refuse cross-company resolution
(DR-003).

## `action` (ORM `ChangeProposal`)

| Column | Type | Null | Notes |
|---|---|---|---|
| `decided_via_token_id` | `String`, indexed | yes | Access token that settled the decision through MCP. |

Constraint: composite FK `(tenant_id, decided_via_token_id)` →
`mcp_access_token(tenant_id, id)`, so a decision can only reference a token of its own
company. Tokens are revoked, never deleted, so the reference stays resolvable.

Invariants:

- `decided_via_token_id` is set only together with `decided_at`, and only by the MCP
  approve/reject path.
- `decided_by_user_id` and `decided_via_token_id` are never both set.
- When a failed execution restores a proposal to `proposed`, both are cleared with
  `decided_at` (the existing reset statements are extended).

Proof of use: joined for the decider of every history row, record origin and activity
item (FR-004, FR-007, FR-009, FR-010).

## Unchanged

- `business_event.action_id` and its composite FK to `action` already exist; this
  feature only fills it for more tools (DR-001).
- No record, document or line table gains a decision column.

## Read model: decision attribution (not stored)

```text
decision = {
  id, tool, label, outcome: executed | rejected | executing | proposed,
  decided_at: timestamp | null,
  decider: { kind: "person", name }
         | { kind: "mcp_token", token_name, token_prefix, revoked, issuer: name | null }
         | { kind: "unknown" }
}
```

`kind: "unknown"` covers decisions settled before spec 055, CLI decisions, and
decisions that are still pending. Names resolve only for users who decided a proposal
or issued a token of the same tenant.
