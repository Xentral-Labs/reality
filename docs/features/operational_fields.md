# Feature: Proven Operational Fields

## Principle

Typed columns exist only for repeated joins, filters, calculations, constraints,
or operational decisions. External detail remains in immutable SourceRecord
payloads. Document fields describe evidence; delivery, reservation, fulfillment,
open quantity, and risk remain derived from Reality.

## Document

`ordered_at`, `requested_delivery_at`, `customer_reference`, `sales_channel`,
`payment_term_id` and `ship_to_party_id` are typed evidence fields.

## DocumentLine

`unit`, `requested_at`, and `line_type` are typed. Currency is inherited from the
Document and is not duplicated.

Existing manual lines are corrected through the shared full-snapshot operation using
opaque line IDs and a derived concurrency revision. The correction is transactional and
audited. Economic changes are blocked after the Document or a line has linked Reality;
presentation/reference corrections do not mutate downstream records. External lines
remain governed by immutable SourceRecord versioning.

## Item

`item_type`, `tracking_type`, `default_location_id`, `purchase_unit`,
`conversion_factor`, and `lead_time_days` drive inventory and purchasing logic.
Only stocked items may have physical Movements. Conversion factors must be
positive and lead time cannot be negative.

## Party and roles

Party carries `accounting_code`, `payment_term_id`, `default_currency`,
`credit_limit`, and `tax_identifier`. PartyRole supports the tenant-scoped roles
`company`, `customer`, and `supplier`, including more than one role per Party and
an optional role-specific `default_location_id`. The legacy Party `type` column is
maintained only as a compatibility shadow during the V0 migration; PartyRole is
the canonical role source.

## Payment terms

PaymentTerm is tenant-scoped master data with an opaque identity, a unique lookup
`code`, display `name`, non-negative `due_days`, lifecycle state, and optional
SourceRecord. Party and Document use `payment_term_id`; the human code is never a
foreign key. Referenced terms are deactivated instead of overwritten so historical
transactions retain their agreed condition.

## Pricing

Sales and purchase pricing share tenant-scoped PriceList and PriceListEntry
structures. Direction, currency, validity, unit, and minimum quantity are typed
because price resolution filters and calculates with them. Direct PartyPriceList
assignments take precedence over PartyGroupPriceList assignments, which take
precedence over the one default list for a direction and currency. Within a list,
the highest applicable quantity tier wins. DocumentLine stores the agreed price
and may link to the PriceListEntry that explained it; later list changes never
rewrite Evidence or downstream Reality. When a caller supplies that optional opaque
entry ID, the shared service re-resolves the document's party, direction, currency,
effective time, item, quantity, unit, and price before recording the line atomically.
Manual agreements deliberately retain no invented pricing provenance. Percentage discounts and free-goods rules are explicitly out of
scope for this first pricing increment.

## Business events

BusinessEvent is the immutable transactional outbox for committed domain changes.
It has an opaque identity plus a tenant-local monotone processing sequence, a
versioned JSON payload, subject, timestamps, and optional source/action/causation
links. It announces Reality changes but does not replace Movement, LedgerEntry, or
other source-of-truth records. The fulfillment queue, fulfillment blockers, and
item supply/demand views are materialized into generic, tenant-scoped projection
rows. Their checkpoints store the latest incorporated tenant-local event sequence
and projection version. They are rebuildable read caches only; invariant-enforcing
commands continue to query authoritative Reality records.

Confirmed Playground-compatible tools pass the existing proposal ID through to these
events, also when used in a normal company. A shipment emits its Movement event and
causally linked Reservation consumption, active-remainder creation when needed, and
Commitment fulfilment on the actual transition. They commit with the domain changes;
the remainder is not a second user allocation. See [Learning Playground](learning-playground.md)
for the attribution contract and remaining run-orchestration work.

The canonical vocabulary is split across `packages/reality-core/config/command_catalog.yaml`,
`business_event_catalog.yaml`, `projection_catalog.yaml`, and `fact_catalog.yaml`.
Contributors add a concept to its matching catalog and run the application-catalog
tests; missing, stale, duplicate, and invalid references fail. Event invalidation sets
describe affected read models, while V0 may still rebuild all operational Projections
lazily after any new tenant Event rather than running selective workers.

## Location

Locations support `parent_location_id`, `source_record_id`, and `allows_stock`.
Parents are tenant-owned and cycles are rejected. Physical Movements cannot use a
Location that disallows stock.

## Commitment

`due_at` is an optional UTC datetime. `created_at` remains the creation timestamp;
`cancelled_at` records cancellation and `priority` is one of `low`, `normal`,
`high`, or `urgent` with `normal` as default.

## Migration defaults

Existing Items become `stocked`, untracked, with purchase unit `pcs`, conversion
factor 1, and zero lead time. Existing Locations allow stock. Existing
Commitments receive normal priority, retain their ISO due value as a datetime,
and existing Party types are backfilled into PartyRole.

## What the Command Catalog Guarantees

Every service the tenant isolation catalog classifies as a mutation and that is reachable from an
endpoint, an agent tool or the CLI is either a declared command, a related service of one, or
listed under `reachable_mutations_that_are_not_commands` with the reason it is not.

The population is two already-gated facts intersected. What mutates comes from the isolation
catalog, which is complete by discovery. What is reachable comes from reading the surface
modules. Neither is a new list, because a hand-maintained list falling behind is the failure this
gate exists to prevent — spec 091 found booking an invoice implemented, tenant-scoped, proven and
reachable from nothing.

**The gate fails in both directions.** An undeclared operation fails it, and so does an exemption
naming a service that is no longer a reachable mutation: a stale entry is how a list like this
rots, because the operation it named goes away, the entry stays, and the next operation with that
name inherits a silence nobody chose.

What it does not do: gate reads, which have their own completeness rules in the capability
guidance; gate the internal building blocks commands are made of, which are mutations and are not
things anybody invokes; or say which surfaces an operation should have.

Its honest limit is that reachability is detected textually rather than semantically, and that an
exemption is a claim somebody made. Each exemption is one line in a reviewed file, which is the
whole difference between this and an absence nobody can see.
