# Data Model

No entity, column, relationship or migration is added.

- SourceRecord: immutable changed payload with existing version and stream identity.
- SourceStream: latest accepted source remains current, even when not interpreted.
- ImportJob: pending → completed with no next_attempt_at for a review result.
- InterpretationOutcome: needs_review plus safe explanation; no produced references.
- Document, DocumentLine, Commitment, Reservation, Movement, LedgerEntry: unchanged
  when processing a guarded update.

Completed review reprocessing is a no-op. Explicit retry moves the job to pending and
the next attempt records review again. Existing successful interpretation is returned.
