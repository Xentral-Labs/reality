# Data Model
No schema changes. Payment Document links an optional original SourceRecord. Two LedgerEntry
records link payment document; SettlementAllocation links the payment control entry directly
to the invoice control entry. ChangeProposal stores review/receipt. Existing attributed events
preserve creation evidence. Current open balance and allocation activity remain derived.
Proposal states remain proposed, executing, executed or rejected with existing recovery rules.
