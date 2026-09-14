# Data model

No schema changes. ChangeProposal stores reviewed intent/reference snapshot and receipt.
Manual SourceRecord retains all supplied fields including gross_amount. Document and
DocumentLine hold stated agreement; each line has one customer/supplier Commitment.
Immutable order.recorded event binds normalized creation snapshot and exact opaque IDs
to its action. Later operational changes are read separately from creation evidence.
