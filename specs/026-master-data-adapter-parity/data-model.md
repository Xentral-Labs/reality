# Data Model: Master Data Adapter Parity

## Persistence decision

No persisted entity or schema change is introduced. Existing Party, PartyRole, Item,
Location, SourceRecord, Evidence, and Reality records remain authoritative.

## Existing entities under comparison

- **Party**: tenant, name, roles and role-default Location meaning, accounting and
  commercial fields, lifecycle, and optional source provenance.
- **PartyRole**: normalized role set for one Party; generated row IDs/order excluded.
- **Item**: tenant, SKU, name, units, type, tracking, default Location meaning,
  conversion, lead time, lifecycle, and optional source provenance.
- **Location**: tenant, name, type, parent meaning, stock permission, lifecycle, and
  optional source provenance.
- **SourceRecord**: source system/type, external ID, full payload meaning, and version
  relation; generated ID/time/serialization formatting excluded.

## Test-only concepts

### Capability matrix row

Record family, lifecycle operation, interface, authoritative service behavior, and
executable evidence identifier. Exactly 36 unique rows exist. It is not a business table.

### Canonical domain snapshot

Family/scenario/tenant aliases, normalized business fields, relationship aliases backed
by opaque IDs, roles, lifecycle, full optional source provenance, and historical-link
digests. It never becomes an application API or persisted aggregate.

## State transitions

```text
absent --create--> active --deactivate--> inactive --reactivate--> active
                         ^                      |
                         |------ update -------|
```

Update preserves identity. Lifecycle changes only applicability. Rejections leave both
tenant snapshots unchanged.

## Validation invariants

- Every record and relationship is tenant-owned; foreign IDs behave as not found.
- Existing shared services own required fields and operational constraints.
- Deactivation never deletes or rewrites linked Source, Evidence, or Reality.
- Canonicalization removes transport noise but never a supported business field.
