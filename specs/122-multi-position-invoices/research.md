# Research
Independent read-only research confirmed DocumentLine already supports N lines per document, each with billed_document_line_id. No billing-reference unique constraint is appropriate because credits also reference order lines.
Decision: same-order multi-position input, independent header amount and stated per-line amounts. Reject mixed/duplicate/already-billed lines, preserve submitted order, lock sorted IDs. Alternative multi-order consolidation and repeated partial invoicing are separate scopes.
Decision: retain single-position behavior and stored review shape; generalize receipt proof only for new plural input. Existing credit path remains separate. Existing invoice.recorded and document.recorded events contain sufficient immutable evidence. No new schema/event needed.
