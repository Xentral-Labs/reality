# Data Model

No schema change. Item, Movement, Reservation, StockBlock, Commitment, CommitmentRevision and MovementCorrection remain authoritative tenant-scoped records.

Physical is movement inflow minus outflow. Reserved and blocked are active quantities. Available is physical minus reserved minus blocked. Incoming is effective outstanding, non-cancelled supplier delivery quantity. Projected is available plus incoming. Location scope applies to each contribution separately.

No observation becomes a Fact or a document status. Existing movement IDs remain the explanation path.
