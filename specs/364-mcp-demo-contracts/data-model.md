# Data Model

No schema change. Existing ChangeProposal retains the existing `_delivery_review`
snapshot/fingerprint before decision. Existing immutable receipts keep projection basis.
Current adapter responses may include derived callable guidance and confirmation
arguments; those are not stored as authority. Shipment Movements are read from existing
tenant-scoped discovery. Chat access restrictions exist only for the current turn.
