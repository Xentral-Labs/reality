# Data Model: Controlled Fact Observation

## Fact

An append-only observation about one existing tenant-scoped subject.

| Field | Contract |
|---|---|
| `id` | Opaque Fact identity. |
| `tenant_id` | Owning tenant; every read and relation is scoped by it. |
| `subject_type` | Cataloged internal Reality subject type. |
| `subject_id` | Opaque ID of an existing same-tenant subject. |
| `predicate` | Stable reviewed predicate from the Fact catalog. |
| `value` | Deterministically serialized, human-readable canonical scalar. |
| `observed_at` | UTC time represented by the observation operation. |
| `source_record_id` | Required by all new writes; direct same-tenant immutable source link. |
| `request_fingerprint` | Hash-derived tenant-scoped retry identity; nullable only for legacy rows. |

Unique constraint: `(tenant_id, request_fingerprint)`. A repeated fingerprint is successful only when all canonical observation content matches the stored Fact.

## Fact Predicate

A configuration contract, not a business table. It defines predicate name, permitted subject types, logical value type, and optional enum values. The first predicate retains the already-proven Shopify example `order.shipping_priority` for a Commitment subject with `standard` and `express` values.

## Relationships

```text
SourceRecord 1 ──< Fact >── 1 cataloged subject
                       |
                       └── emits exactly one BusinessEvent

ChangeProposal ──confirms──> fact_observe application tool
```

Document and DocumentLine may exist between SourceRecord and interpretation, but Fact does not duplicate their IDs. Inspector traverses the direct source relationship.

## Lifecycle

Facts are append-only. They are never updated or deleted by this feature. A later or corrected observation is a new Fact with a distinct idempotency identity and observation time. Selecting a current belief or promoting an observation into typed Reality is outside this feature.
