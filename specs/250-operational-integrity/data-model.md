# Data Model: Operational Integrity

No migration or new entity is planned. This feature strengthens transitions and correlations among existing tenant-scoped records.

## Movement

The arrived `return` Movement is physical authority. A resolving `transfer`, `adjustment`, or `supplier_return` Movement takes its source from the arrival destination, inherits applicable handling-unit, lot, and serial identity, and links directly through `resolves_movement_id`. It remains append-only and independently correctable. Uncorrected resolving quantity cannot exceed arrived quantity.

## Commitment and CommitmentRevision

Commitment retains original quantity, parties, item, exact location, status, and optional evidence. CommitmentRevision append-only records a later stated date and/or positive quantity. Effective quantity is derived from the latest applicable statement.

Transitions are open → fulfilled when derived open becomes zero, and open → cancelled through explicit cancellation of the open remainder. Fulfilled/cancelled commitments cannot be revised or cancelled again. Document lifecycle does not participate.

## Reservation

Reservation remains an exact-location, optionally tracked allocation linked only to one customer Commitment. Status remains active, consumed, or released.

For an unambiguous downward revision, active quantity within revised open remains, excess releases, and a partially retained homogeneous allocation is represented by releasing the original and recording an exact retained allocation with identical item/location/tracking identity in the same transaction. Heterogeneous allocations require explicit retained quantities keyed by existing opaque reservation IDs; confirmation rejects stale or identity-altering selections.

After successful revision/cancellation, active reserved ≤ derived open; after cancellation it is zero.

## CommitmentHold

Cancellation or revision settlement releases active holds by timestamp while retaining reason, note, creator, and creation time. Holds never represent cancellation.

## ChangeProposal

Lifecycle remains proposed → executing → executed or proposed → rejected. Executing may be genuinely unknown. Known pre-effect refusal remains proposed; proven rolled-back failure returns to proposed only under a no-effect contract; exact recorded effect reconciles to executed; insufficient evidence remains unresolved.

## BusinessEvent and SourceRecord

Cancellation event evidence records action correlation, reason, released reservation/hold IDs, fulfilled quantity, and cancelled remainder. Optional SourceRecord retains a received external/manual statement. Return disposition evidence explains the resolving Movement. Human numbers never establish identity.
