# Contract: Master Data Update Proposals and Audit Events

## Common proposal behavior

- Tools: `party_update_propose`, `item_update_propose`, `location_update_propose`.
- Input is `{ "records": [...] }` with at least one same-family record.
- Every record requires opaque `id`; display references assist discovery only.
- Schemas reject unknown fields.
- Preview reads tenant-scoped state and stores an `expected_revision` per target without mutation.
- Approval rechecks every revision and executes atomically.

## Supported records

- **Party** required: `id`, `name`, `type`, `roles`; optional: `accounting_code`, `payment_term_code`, `default_currency`, `credit_limit`, `tax_identifier`, `source_system`, `external_id`, `source_payload`.
- **Item** required: `id`, `sku`, `name`, `unit`; optional: `item_type`, `tracking_type`, `default_location_id`, `purchase_unit`, `conversion_factor`, `lead_time_days`, `source_system`, `external_id`, `source_payload`.
- **Location** required: `id`, `name`, `type`; optional: `parent_location_id`, `allows_stock`, `source_system`, `external_id`, `source_payload`. Parent IDs are opaque existing Location IDs.

## Result and failures

Executed output lists updated family/ID pairs. Any invalid, missing, cross-tenant, duplicate, or stale target fails the entire batch. A no-op target emits no false event.

## Event contract

Event types remain `party.updated`, `item.updated`, and `location.updated`:

```json
{"changes":{"name":{"before":"Old","after":"New"}}}
```

The subject is the stable master-data ID. `action_id` identifies the executing proposal. Historical events may omit `changes` and remain readable.
