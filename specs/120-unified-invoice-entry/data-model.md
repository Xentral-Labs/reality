# Data Model
No new tables/columns. Invoice DocumentLine.billed_document_line_id points to its order line.
Document links source; LedgerEntry links invoice/source. ChangeProposal stores intent/review and
receipt. Attributed invoice.recorded BusinessEvent stores normalized creation and exact receipt.
Proposal transitions remain proposed → executing → executed; rejected and unresolved semantics
are unchanged. Human invoice numbers are labels, never identity.
