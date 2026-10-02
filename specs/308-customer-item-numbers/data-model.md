# Data Model: Customer Item Numbers

## `customer_item_number` (new)

| Column | Type | Notes |
|---|---|---|
| `id` | text | PK with `tenant_id` |
| `tenant_id` | text | Tenant FK |
| `party_id` | text | The customer; composite FK |
| `item_id` | text | Our item; composite FK |
| `customer_item_number` | text | As the customer states it |
| `match_key` | text | Upper-case, without spaces; what lines are matched on |
| `customer_item_name` | text | The customer's name for it, as stated |
| `source_record_id` | text | The statement in force; composite FK |
| `created_at`, `updated_at` | timestamptz | |

**Constraints:**
- unique `(tenant_id, party_id, match_key)`;
- `btrim(customer_item_number) <> ''`.

**Indexes:**
- `(tenant_id, item_id)`;
- `(tenant_id, source_record_id)`.

**Events:** `customer_item_number.set` and `customer_item_number.removed`.

**Line payload key:** `customer_item_number`, the number the line was ordered by, as stated.
