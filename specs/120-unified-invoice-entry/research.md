# Research

Decision: preserve canonical one-order-line invoice semantics. Independent read-only research
confirmed quantity <= ordered quantity, positive stated gross amount, no fulfillment prerequisite,
and any existing billing link prevents further invoicing. Alternative multi-line consolidation or
remainder invoicing would expand core semantics and is deferred.

Decision: use existing proposal lifecycle with invoice-specific proof. Sales posts receivable debit
and revenue credit; purchase inventory debit and payable credit. Existing atomic service returns
source/document/line/two ledger IDs. Add an attributed immutable snapshot for unknown recovery.
Do not bind execution-time default `now()` into a repeatedly regenerated token.

Decision: reuse searchable evidence documents and their inspector lines rather than requiring a
shipment commitment. Historical creation proof must remain valid after allocations and reversals.
Protect shared credit service and practice policy; add financial rollback and current-state tests.
