# Rehearsal state and shortest links

No persistent schema changes. Simulation state is run-local expected evidence, not an alternative production ledger.

- Authored customer request: source ID/number, item, recipient/address, quantity, source-stated order/billing/payment amounts and ordinal deadline. Future cancellation/return/payment behavior stays private until released.
- Accepted order references: document, document-line, commitment and source opaque IDs returned by the normal tool or reviewed intake.
- Purchase reaction: accepted pack quote, issued day, promised receipt offsets and private actual supplier receipt offsets. Operators see quoted dates and accepted fulfilled quantities; revised future dates become visible only after a released supplier notice.
- Dispatch reaction: exact shipment/package IDs, commanded recipient/address, quantity and simulated ETA. Actual service observation verifies retained destination, package delivery and explicit structured failure. Correct destination is a separate business objective.
- Return: announcement → original customer commitment; arrived movement → announcement. Financial credit/refund remains separate and cannot change original fulfilled quantity.
- Finance action: author-stated amount/role pair, accepted exact ledger-entry IDs, counterparty/document identity and expected allocation target. Per-account debit-minus-credit expectations remain independent of read observations.
- Held provider funds: payment document and independent unallocated amount, read through canonical payment_rows. These are distinct from invoice/credit open balances and source lines with unknown customer references.
- Payout: immutable provider statement and line sources, bank/clearing accounts, known charge/refund/fee posting groups and unmatched raw lines. Bank deposit cannot substitute for individual customer payment evidence.
- Review boundary: exact pending proposal/payload digest and principal-attributed approval. No boolean/read-only capability is treated as approval.

- Local correspondence: immutable Source payload with explicit existing party/document references when available; unique run-local message/thread/reply IDs and `transport: local_simulation`. Journal retains exact source ID, ordinal day, direction and recorded state. The source is communication evidence, never fulfillment or mail authorization. Built-in outgoing records are simulated; explicit custom replies are proposed drafts. Existing Sources are not rewritten to add later order IDs.
