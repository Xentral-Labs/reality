# Data Model: Customer Exchange

## customer_exchange (new)

A confirmed statement that one replacement promise settles a quantity of one customer return
instead of a credit. Reality, append-only: an exchange is never edited; cancelling its
replacement ends its effect at read time.

| Column | Type | Rule |
|---|---|---|
| `tenant_id` | string | FK `tenant.id`; part of the primary key |
| `id` | string | opaque, prefix `cex` |
| `return_movement_id` | string, nullable | composite FK `movement`; a movement of type `return` with a commitment |
| `return_announcement_id` | string, nullable | composite FK `return_announcement` |
| `replacement_commitment_id` | string | composite FK `commitment`; a document-less `customer_delivery` with amount 0 |
| `quantity` | numeric(18,4) | exchanged quantity of the returned item, `> 0` |
| `reason` | text | stated reason, not empty |
| `source_record_id` | string | composite FK `source_record`; the manual source of the confirmed request |
| `created_at` | UTC timestamp | |

Constraints:
- `PRIMARY KEY (tenant_id, id)`.
- `CHECK ((return_movement_id IS NULL) <> (return_announcement_id IS NULL))`: exactly one return side.
- `CHECK (quantity > 0)`.
- `UNIQUE (tenant_id, replacement_commitment_id)`: one exchange per replacement.
- `UNIQUE (tenant_id, source_record_id)`: request replay is idempotent.
- Indexes: `tenant_id`; `(tenant_id, return_movement_id)`; `(tenant_id, return_announcement_id)`;
  one per foreign key's first column (spec 181 FR-001).

Not stored (DR-002): party, item and original order line (from the return's commitment), the
replacement item and quantity (on the replacement commitment), the confirming decision (the
source record's external id is the proposal id, as for return dispositions).

## Derived values (read time, never stored)

- **exchanged quantity of a delivery**: sum over exchanges whose return belongs to that
  delivery and whose replacement is not cancelled; for a cancelled replacement, the part its
  shipments cover.
- **exchanged and arrived**: the exchanged quantity capped by what came back: the return
  movement's quantity, or what arrived against the announcement.
- **exchangeable quantity of a return**: for a movement, its quantity minus exchanges on it;
  for an announcement, its quantity minus exchanges on it; in both cases also bounded by the
  delivery's returned-or-announced quantity minus credited and exchanged.

## Changed records

None. `commitment`, `movement`, `return_announcement` and `document` gain no columns.

## Migration

`0101_customer_exchanges` after `0100_business_journey_proposals`: create the table, checks
and indexes; downgrade drops it. No data migration.
