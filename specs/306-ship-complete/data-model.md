# Data Model: Ship-Complete and No-Backorder Rules

## `delivery_rule` (new, append-only)

| Column | Type | Notes |
|---|---|---|
| `id` | text | Opaque ID, PK with `tenant_id` |
| `tenant_id` | text | Tenant FK |
| `party_id` | text, null | The customer the rule is for; composite FK |
| `document_id` | text, null | The order the rule is for; composite FK |
| `rule` | text | `partial_allowed`, `ship_complete`, `no_backorders` |
| `reason` | text | Required, non-blank |
| `stated_by` | text | Who stated it |
| `stated_at` | timestamptz | When |
| `action_id` | text, null | The confirmed proposal |

Checks: exactly one of `party_id` and `document_id`; `rule` in the three values; `reason` not blank. Indexes: `(tenant_id, party_id, stated_at)` and `(tenant_id, document_id, stated_at)`.

Event: `delivery_rule.stated`.

Derived at read time, never stored:
- the effective rule of an order;
- whether an order is complete;
- which orders wait for completeness;
- which rests are backorders against the rule.
