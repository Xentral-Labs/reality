# Data Model: Demo Entrypoint Equivalence

## Persistence decision

No new persisted entity, field, relationship, constraint, index, or migration is needed.
The manifest and semantic aliases are test/contract projections only.

## Existing authoritative records

- **Demo tenant**: owns every record for one run and receives an owner membership through Web.
- **Reference data**: company/customer/supplier Parties, Item, and Location.
- **Source and Evidence**: immutable Shopify SourceRecord, Document, DocumentLine, and
  every Fact or other Evidence family observed by the pre-implementation inventory.
- **Reality**: opening Movement, outgoing/incoming Commitments, and Reservation; inventory
  and fulfilment remain derived.
- **Explanation context**: existing ChatSession/Messages, BusinessEvents emitted by the
  real flow, and normal Inspector links.

## Test-only canonical manifest

| Section | Included meaning | Allowed normalization |
|---|---|---|
| `reference_data` | names, roles/types, SKU, unit, location, lifecycle | opaque IDs → semantic aliases; row order |
| `source` | system, type, external identity, complete payload | ID, timestamps, run-relative dates |
| `evidence` | document/line values and relationships | IDs → aliases; timestamps/order |
| `reality` | commitments, reservation, movement, shortest links | IDs → aliases; timestamps/relative dates |
| `derived` | physical, reserved, available, incoming, projected, fulfilment, explicit financial zero state | decimal representation only |
| `explanation` | trace categories and shortage explanation meaning | IDs and presentation formatting |

## State transitions

```text
empty tenant → confirmed demo → canonical state → rerun → same state
empty tenant → empty-company choice → empty tenant
populated tenant → demo request → original state preserved
```

## Validation invariants

- Every row and read is tenant-scoped; Source payload remains lossless and immutable.
- Documents remain Evidence and operational values remain derived from Reality.
- Alias maps preserve topology and never become production identity.
- The manifest exposes an explicit version and every actually produced record family.
- Cancellation and empty-company creation produce no demo records.
- Completed reruns do not change canonical state or counts.
- Partial failure remains visible and is not claimed to be safely retryable.
- No model or migration file changes are permitted.
