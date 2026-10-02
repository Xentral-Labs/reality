# Data Model: Ship-Complete and No-Backorder Rules

## `delivery_rule` (new)

The rule in force for one customer or one order. Every statement about it is a version of one source stream per subject (spec 320 pattern): `internal_delivery_rule` / `delivery_rule` / `party:<id>` or `document:<id>`. The row names the version in force, and the history is the stream.

| Column | Type | Notes |
|---|---|---|
| `id` | text | Opaque ID, PK with `tenant_id` |
| `tenant_id` | text | Tenant FK |
| `party_id` | text, null | The customer the rule is for; composite FK |
| `document_id` | text, null | The order the rule is for; composite FK |
| `rule` | text | `partial_allowed`, `ship_complete`, `no_backorders` |
| `reason` | text | Required, non-blank, as stated |
| `source_record_id` | text | The statement in force; composite FK, required |
| `created_at`, `updated_at` | timestamptz | |

**Checks:**
- exactly one of `party_id` and `document_id`;
- `rule` is one of the three values;
- `reason` is not blank.

**Uniqueness and indexes:**
- partial unique indexes on `(tenant_id, party_id)` and `(tenant_id, document_id)`;
- an index on `(tenant_id, source_record_id)`.

**Event:** `delivery_rule.stated`, with the previous rule and the source record.

Restating replaces the row's values and names the new version. Lifting the rule for an order is stating `partial_allowed` for it, so the order keeps an explicit rule.

**Derived at read time, never stored:**
- the effective rule of an order;
- whether an order is complete;
- which orders wait for completeness;
- which rests are backorders against the rule.
