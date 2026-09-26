# Feature: Master Data Lifecycle

## Goal

Manage tenant-owned Parties, Items, and Locations consistently through the web,
CLI, and JSON API while preserving historical Reality links.

## Behavior

- Create and update operations call shared application services.
- Records are never deleted through the supported interfaces. Deactivation sets
  `is_active=false`; reactivation sets it back to `true`.
- Inactive records remain readable and linked to existing evidence and Reality.
- Every lookup and mutation is tenant-scoped.
- Names and typed fields required by core behavior must not be blank.
- Parties and Items may point to one current immutable SourceRecord containing
  their source system and external ID. A changed external reference creates a new
  SourceRecord; the old source truth is never overwritten. Manual records may
  remain without a source.
- Operational screens expose only source system and external ID. Raw source data
  remains available through the Inspector.

## Interfaces

- Web: create from each register; edit and change lifecycle state on detail pages.
- CLI: `create`, `update`, `deactivate`, and `activate` below `party`, `item`, and
  `location`; all accept `--tenant` or use the selected tenant.
- JSON API: tenant-scoped collection `GET`/`POST`, record `GET`/`PUT`, and
  `PATCH .../active` endpoints below `/api/tenants/{tenant_id}`.

API mutations return the resulting record. Invalid input returns HTTP 400 and a
missing or cross-tenant record returns HTTP 404.

Adapter parity compares reloaded canonical business state, not presentation output.
CLI and JSON API call the same Party, Item, and Location services; Product Web uses the
JSON API and owns only form, loading, and error presentation. Generated IDs, timestamps,
Rich text, and HTTP envelopes may differ, while business fields, relationships,
lifecycle, tenant ownership, and complete optional SourceRecord provenance must match.

## Acceptance criteria

- Equivalent operations through web, CLI, and API produce the same domain state.
- Cross-tenant updates and lifecycle changes cannot access a record.
- Existing records migrate as active.

## Early Payment Discounts

A `PaymentTerm` carries `due_days` and, optionally, `discount_percent` and `discount_days` —
the two figures that make an early-payment discount. Both are received values: a company states
"two per cent if you pay within ten days" and Reality records it as stated.

Both columns are nullable, and null in both is the statement that this term grants no discount.
A zero rate would say "nothing off", which is a different claim. Either figure alone is refused:
a rate without a window says nothing about when it applies and a window without a rate says
nothing about what it is worth, so half a discount condition is not a condition.

The rate is stored to three decimal places, which is past anything trade quotes, so a stored
rate is never a rounded version of the rate somebody stated. Nothing in the product ever
multiplies it out into a money figure — see
[operational exceptions](./operational_exceptions.md) for why.

# Explicit prepayment policy

Payment terms carry `requires_prepayment` as an explicit tenant-scoped boolean. Existing and newly
created terms default to false unless the caller states otherwise; no migration or service infers
the policy from the term code, translated name or due days. The policy is available through the
shared service, HTTP API, CLI, application tools and MCP schema.
