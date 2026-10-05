# Existing read contracts
**Language**: English
Readiness adds payment_interpretation with amount_basis (kind, amount, currency, document_id), payment_evidence (status, received, remaining, invoice_ids, allocation_ids), shipment_constraint (status, blocker_codes, release_id), and notice. Standard evidence is not_evaluated with null received/remaining. Unstated and ambiguous evidence also use null interpreted amounts; missing invoice amounts remain qualified canonical amounts, not global payments. Constraint statuses: not_applicable, not_required, blocked, released, satisfied. Blocked takes precedence over release for surviving payment conditions.
Discovery summary adds selection_record_count: integer only if complete_matching_selection is true; otherwise null. No new input or tool. Legacy numbers, cached payloads and dispatch review hashes are unchanged.

Queue standard lines retain their existing null readiness; consumers use the existing direct readiness tool for standard order payment interpretation. Prepayment queue readiness shares the same helper. No new per-line query or cached field is introduced.
