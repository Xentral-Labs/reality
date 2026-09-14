# Data Model: Auditable Master Data Updates

No table or column is added. Existing fields remain the proven update surface.

## Canonical snapshots

- **Party**: `name`, `type`, unique `roles`, `accounting_code`, nullable `payment_term_id`, uppercase `default_currency`, decimal-string `credit_limit`, `tax_identifier`, nullable `source_record_id`.
- **Item**: `sku`, `name`, `unit`, `item_type`, `tracking_type`, nullable `default_location_id`, `purchase_unit`, decimal-string `conversion_factor`, `lead_time_days`, nullable `source_record_id`.
- **Location**: `name`, `type`, nullable `parent_location_id`, boolean `allows_stock`, nullable `source_record_id`.

## Change Proposal update record

- Required opaque target `id`.
- Complete intended values accepted by the family update contract.
- Server-generated `expected_revision` of reviewed normalized state.
- Optional source provenance preserving lossless payloads.
- Duplicate targets rejected; same-family batch executes in one transaction.

## Business Event payload

- `changes` keyed by canonical audit field.
- Each entry contains exactly `before` and `after`.
- Decimals are canonical strings; boolean, integer, null, list, and opaque-ID values retain JSON types.
- Unchanged fields are absent; compatibility summaries may coexist.
- `action_id` links an executing proposal; `source_record_id` links resulting source provenance.

## State transitions

```text
current + valid direct update -> normalized change + immutable event
current + proposal -> proposed without mutation
proposed + matching confirmation -> normalized change + executed proposal + linked event
proposed + stale/invalid/cross-tenant confirmation -> no master-data/event mutation
```
