# Data model

No persistence change. Existing Commitment, CommitmentRevision, Movement, MovementCorrection, Reservation, Document, DocumentLine and Item records supply one evaluation. The existing ProjectionRow and ProjectionCheckpoint continue to store disposable financial read results. All access is tenant-scoped; no new relationship or state transition.
