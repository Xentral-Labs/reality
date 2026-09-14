# Data Model: Physical Shipments and Tracking

## Shipment

Opaque `id`, `tenant_id`, `direction` (`inbound|outbound`), `purpose`
(`customer_delivery|supplier_delivery|customer_return|supplier_return`), `counterparty_id`,
optional `source_record_id`, UTC `created_at`. Direction/purpose/PartyRole is constrained. No
status or Document/Line fields. One Shipment owns one or more Packages.

## ShipmentPackage

Opaque `id`, `tenant_id`, `shipment_id`, optional received `carrier`, `tracking_number` and
`source_record_id`, UTC `created_at`. Tracking is searchable text, not identity or globally unique.
Untracked Packages are valid.

## ShipmentEvent

Opaque `id`, `tenant_id`, `shipment_id`, optional `shipment_package_id`, closed `event_type`,
`reporter_type`, optional UTC `occurred_at`, UTC `recorded_at`, optional `location_text`,
`source_record_id`, and `external_event_id`. All targets share tenant/Shipment. Date-only source
values stay payload. External identity supports scoped idempotency but is not record identity.

## ShipmentEventSupersession

Opaque `id`, `tenant_id`, `superseded_event_id`, optional `replacement_event_id`, `reason`,
`actor_context`, optional `source_record_id`, UTC `created_at`. Original events are immutable; an
event is currently superseded at most once; replacement is optional for retraction.

## Movement extension

Nullable `shipment_package_id`; null remains valid. Compatibility:

| Purpose | Direction | Movement |
|---|---|---|
| customer_delivery | outbound | `shipment` |
| supplier_delivery | inbound | `receipt` |
| customer_return | inbound | `return` |
| supplier_return | outbound | `supplier_return` |

Every existing Commitment, return, Location, tracking, stock and correction rule remains active.

## Derived observations and indexes

Queries use effective Movements and non-superseded events and return component evidence, preserving
mixed Package state. Add tenant-first indexes for Shipment date/direction/purpose/party,
Package Shipment/carrier/tracking, Event Shipment/Package/external identity, and Movement Package.
Choose text-search index from measured PostgreSQL plans. No derivation is stored.

## Migration

Add tables and nullable FK without backfill. Forward/backward tests prove historical Movement truth
unchanged. Downgrade removes feature data only after writers stop and removal is approved.
