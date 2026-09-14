# Research: Auditable Movement Corrections

## Decision 1: One explicit correction relation

**Decision**: Add one tenant-scoped `MovementCorrection` relation connecting original,
exact compensation, and optional replacement Movements, with reason, correction time,
actor context, and canonical request fingerprint.

**Rationale**: The relationship is repeatedly needed for uniqueness, retry, derived
fulfilment, filtering, role/status, audit, and explanation. Keeping the context together
enforces one coherent chain without adding mutable fields to immutable Movements.

**Alternatives considered**:

- Self-FKs plus context fields on Movement: spreads one operation across several rows
  and weakens coherent-chain constraints.
- A corrected boolean/status: mutable and redundant with the relation.
- Event payload only: not an authoritative queryable domain relationship.

## Decision 2: Positive exact inverse plus optional replacement

**Decision**: Compensation uses explicit Movement type `correction`, copies the original
item, positive quantity, and tracking identity, swaps source/destination locations, and
links through the correction relation. It does not copy the original Commitment or
SourceRecord; both are reached through the original. Replacement is an ordinary
validated Movement with only its own direct provenance.

**Rationale**: Swapped locations cancel physical stock for every Movement type without
negative quantities. The correction relation supplies the original Commitment
contribution for fulfilment reversal without duplicated provenance. A separate
replacement expresses the intended event and can itself later be corrected. Source
evidence remains honest and direct.

**Alternatives considered**:

- Negative quantity: violates the existing positive-quantity invariant and broadens all
  calculations.
- General adjustment: cannot reliably reverse Commitment fulfilment or explain lineage.
- Reusing the original type with swapped locations: violates normal type/location
  semantics and makes a reversed receipt look like an outbound receipt.
- Mutating the original: destroys the physical journal and audit history.

## Decision 3: One non-committing validation/insertion core

**Decision**: Extract reusable non-committing Movement normalization, validation, and
append helpers. Keep `record_movement` as the normal committing wrapper; preview and
correction call the same helpers and correction commits once.

**Rationale**: Calling the current public recorder twice would commit partial state and
perform shipment Reservation side effects before the entire correction is known valid.
One shared core prevents rule drift and supports failure rollback.

**Alternatives considered**:

- Sequential public recording calls: partial commits are possible.
- Separate correction validation: duplicates inventory rules.
- Browser-calculated inverse: moves business authority into presentation code.

## Decision 4: Canonical fingerprint plus row lock and uniqueness

**Decision**: Lock the tenant-owned original, compute a canonical semantic fingerprint
from correction intent excluding observational actor context, and enforce unique
original/role relationships. Equal retry returns the existing result; divergent retry
raises conflict. The initially accepted actor context remains in audit data.

**Rationale**: This covers lost responses and concurrent operators without trusting a
caller key alone. Database uniqueness remains the race backstop.

**Alternatives considered**:

- Caller-generated idempotency key only: does not prove semantic equality.
- Last-write-wins: permits multiple physical corrections.
- Timestamp comparison: unstable and not semantic identity.

## Decision 5: Correction-aware derivation, not stored status

**Decision**: Derive Movement role/status from `MovementCorrection`; assign compensation
negative fulfilment contribution; keep directional stock arithmetic; derive tracked
identity location from net legs; exclude compensation from unexplained-Movement causes;
reconcile affected non-cancelled Commitment statuses.

**Rationale**: Operational truth remains reproducible from immutable Reality records.
Existing newest-row identity logic and positive-only fulfilment would otherwise produce
incorrect results after correction.

**Alternatives considered**:

- Mutable stock/fulfilment/corrected fields: create competing authority.
- Leaving fulfilment unchanged: stock and operational state disagree.
- Ordering only by replacement occurrence time: historical timestamps can misstate the
  current tracked location.

## Decision 6: Server preview and existing confirmation boundaries

**Decision**: Provide read snapshot, server preview, and atomic execute contracts. Web
and CLI show the preview and explicitly confirm. Chat/MCP use the existing durable
ChangeProposal approval path. All delegate to the same tenant-scoped services.

**Rationale**: Operators see exact consequences without adapters recreating rules, and
mutating agent actions cannot bypass confirmation.

**Alternatives considered**:

- Direct mutation from every adapter: rule drift and confirmation risk.
- Client-only preview: may differ from server validation.
- A new approval subsystem: unnecessary duplication.

## Decision 7: One correction event

**Decision**: Emit exactly one `movement.corrected` event for the atomic operation,
subject to the original Movement and containing the role IDs and audit context. It
invalidates the same consumers as normal Movement recording.

**Rationale**: Consumers need one atomic semantic change, not partially ordered internal
events. All physical records and the relation are available when the event is observed.

**Alternatives considered**:

- Only `movement.recorded` events: correction intent is invisible.
- Separate events for compensation and replacement: consumers can observe or interpret
  a partial correction sequence.

## Decision 8: Guarded downgrade

**Decision**: No backfill is required. Downgrade may drop the table only while it is
empty; after corrections exist, application rollback retains the table and data.

**Rationale**: Removing correction context would turn compensation rows into unexplained
ordinary Movements and corrupt derived meaning.

**Alternatives considered**:

- Unconditional drop: destroys essential domain semantics.
- Copy correction metadata into Movement before downgrade: unnecessary destructive
  migration complexity without a supported legacy representation.
