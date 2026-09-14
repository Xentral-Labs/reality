# Data Model: Chat Master Data Proposals

## Persistence decision

No persisted entity or schema changes are introduced. Existing Party, PartyRole, Item,
Location, SourceRecord, BusinessEvent, and ChangeProposal records remain authoritative.

## Existing entities

- **Party**: Requires a non-empty name and at least one accepted role. Its opaque ID,
  tenant, roles, optional commercial values, lifecycle, and optional SourceRecord link
  retain existing meaning.
- **Item**: Requires non-empty SKU and name. Unit defaults to `pcs`; type, tracking,
  relationship, conversion, lifecycle, and optional SourceRecord semantics remain
  unchanged.
- **Location**: Requires a non-empty name. Type defaults to `warehouse`; parent,
  stock permission, lifecycle, and optional SourceRecord semantics remain unchanged.
- **ChangeProposal**: Stores one exact family tool name and a non-empty ordered records
  list while proposed; confirmation changes it to executed with created opaque IDs.
- **SourceRecord**: Optional immutable provenance. It exists only when a complete source
  identity pair is supplied.

## Proposal state transition

```text
absent → proposed → executed
                  ↘ rejected
```

Only explicit confirmation permits `proposed → executed`; an executed proposal cannot
transition again.

## Batch invariants

- All records in one proposal belong to one family and the confirming tenant.
- The list contains at least one record.
- Every record passes existing service validation before the transaction commits.
- Location `ref` values are unique within a batch; `parent_ref` resolves only to an
  earlier record, and cannot be combined with `parent_location_id`.
- A failure leaves no batch-created master record, role, SourceRecord, or business event.
- Generated opaque IDs are outputs, never user-provided identity.
