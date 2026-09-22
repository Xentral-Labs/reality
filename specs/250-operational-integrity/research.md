# Research: Operational Integrity

## Return identity

**Decision**: Inherit applicable handling-unit, lot, and serial IDs from the arrived return Movement; do not accept them as caller-selected disposition fields.

**Rationale**: The physical event already identifies the goods. Restatement permits drift and violates the shortest link.

**Alternatives considered**: Caller inputs (unsafe mismatch), untracked resolving movement (false identity stock), new disposition table (duplicate authority).

## Downward revision allocation

**Decision**: Atomically release reservation excess only when retained allocation is unambiguous. Release/replace a homogeneous allocation for exact partial retention. For heterogeneous choices, return eligible opaque reservation IDs and require the operator to resubmit exact retained quantities.

**Rationale**: Availability must be true, but revision does not authorize Reality to choose a physical identity.

**Alternatives considered**: Newest-first release (creation order is not authority), retain excess (false availability), refuse all excess cases (unnecessarily blocks common reviewed case).

## Cancellation

**Decision**: Wrap existing `cancel_commitment` in reviewed `commitment_cancel` behavior with required reason, optional source, event correlation, and receipt.

**Rationale**: Commitment already owns cancellation. Missing safe orchestration does not justify Document status or parallel lifecycle.

**Alternatives considered**: Hold (temporary and false backlog), quantity zero (distinct meaning and invalid revision), Document cancellation (violates Reality authority).

## Cancellation reason

**Decision**: Retain reason and affected IDs in the correlated immutable event, with optional SourceRecord; do not add a Commitment column.

**Rationale**: The event explains the occurrence without duplicating lifecycle state.

## Proposal failure boundary

**Decision**: Run possible authorization/stale/validation checks before claim. Restore after claim only for a caught domain failure with established complete rollback and a no-effect action contract. Otherwise preserve executing and reconcile exact evidence.

**Rationale**: Known validation failures must not strand, while process interruption/lost response must remain protected from duplicate replay.

**Alternatives considered**: Reset every exception (duplicate risk), leave every exception executing (permanent blockage), new workflow/failed status (unnecessary schema/infrastructure).

## Migration and repair

**Decision**: No migration and no silent historical repair. Operators use existing correction/release actions.

**Rationale**: Code cannot infer intended historic identity/allocation.

## Adapter parity

**Decision**: Route revise/cancel through the existing delivery review/detail/reconcile framework and regenerate executable catalogs.

**Rationale**: It already supplies confirmation, state binding, recovery, and shared adapter semantics.
