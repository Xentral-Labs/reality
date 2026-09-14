# Data Model: Auditable Movement Corrections

## Persistence decision

Add one tenant-scoped `MovementCorrection` business table. Existing Movement rows and
their positive-quantity schema remain unchanged and immutable. No existing data is
backfilled; absence from the correction relation means role `normal`.

## MovementCorrection

| Field | Meaning and constraint |
|---|---|
| `id` | Server-generated opaque primary identity. |
| `tenant_id` | Required tenant owner; indexed and enforced by every service query. |
| `original_movement_id` | Required Movement FK; unique so one direct correction can succeed. |
| `compensating_movement_id` | Required Movement FK; unique; exact inverse and never directly correctable. |
| `replacement_movement_id` | Optional unique Movement FK; normally validated intended event. |
| `reason` | Required trimmed durable business reason. |
| `corrected_at` | Required UTC time at which the correction was accepted. |
| `actor_context` | Optional bounded canonical serialized context supplied by the authenticated/action boundary. |
| `request_fingerprint` | Required canonical semantic fingerprint; tenant-unique retry identity. |

Database checks require the three Movement role IDs to be pairwise distinct. Service
validation requires all referenced Movements to belong to `tenant_id`; adding composite
tenant FKs would require redundant Movement uniqueness and is not justified.

## Movement roles and relationships

- **Normal**: Not referenced by a correction relation.
- **Corrected original**: Referenced as `original_movement_id`; remains unchanged.
- **Compensation**: Referenced as `compensating_movement_id`; uses explicit type
  `correction`, copies original item, positive quantity, and tracking identities, swaps
  locations, and has no copied Commitment or SourceRecord.
- **Replacement**: Referenced as `replacement_movement_id`; follows normal Movement
  invariants and may later be the original in another correction relation.

The relation is the shortest true correction link between Movements. It adds no
Document or DocumentLine provenance. Each Movement retains only its own direct optional
Commitment and SourceRecord relationships.

## Derived values

- `correction_role` and `correction_status` derive from relation membership.
- Physical stock continues to sum inbound minus outbound Movement legs; swapped
  compensation locations exactly cancel the original.
- Commitment fulfilment sums normal/replacement expected-type quantities and subtracts
  the applicable original contribution reached through each correction relation.
- Open quantity remains commitment quantity minus derived fulfilment, clamped at zero.
- Non-cancelled Commitment status is reconciled to `fulfilled` only when open quantity is
  zero, otherwise `open`.
- Tracked identity presence/location derives from net Movement legs, not newest business
  timestamp.
- Compensation does not independently cause `unexplained_movement`; its correction
  relation explains it.

## Validation

- Original and every referenced entity are tenant-owned; foreign references disclose
  nothing.
- Original is not a compensation and has no existing direct correction.
- Reason is non-empty after trimming; actor context is bounded and canonicalizable.
- Compensation has type `correction`, is the exact inverse, and passes inverse-specific
  tenant, item, positive quantity, location, stock, and tracking validation against later
  history; normal Movement type/location-shape rules do not apply to it.
- Replacement passes normal item, positive quantity, direction, location, stock, hold,
  Commitment, SourceRecord, lot, serial, and handling-unit validation against the atomic
  post-compensation state.
- Original, compensation, replacement, relation, Commitment reconciliation, and event
  persist together or not at all.

## Retry and state transitions

```text
eligible original + preview → no persistent change
eligible original + confirmed valid request → corrected chain + one event
same original + same fingerprint → existing chain, no new effect
same original + different fingerprint → conflict, no new effect
compensation selected → rejected, no new effect
replacement selected later → new independently linked correction chain
dependent later history prevents inverse → rejected with correction-order guidance
```

## Migration and rollback

Migration `0028_movement_corrections` creates the table, constraints, and indexes. No
backfill occurs. Upgrade precedes application deployment. Downgrade may drop the table
only when empty; once corrections exist, rollback keeps the table because its links are
required to interpret the appended Movement history.
