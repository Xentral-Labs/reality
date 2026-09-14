# Research decisions
- Reuse existing typed billed_document_line_id for credit→invoice→order, preserving credit→order legacy. Rejected source-JSON identity for recurring capacity joins and redundant schema fields. Read-only research agent audited core, exceptions and Playground readers.
- Financial credit does not require physical return; existing post_sales_credit_note already separates those concepts. Legacy return entitlement recognizes descendant credits to prevent duplicated credit of returned goods.
- Legacy order-linked credit cannot identify which invoice it credits. Block affected new selections and disclose the existing evidence; do not infer allocation.
- Existing exception pricing readers already exclude credit documents, so their direct order comparison remains correct. Reversal billing effects only traverse sales/supplier invoices, not credits. Playground invoice state needs descendant credit identities in its stale snapshot.
- Explicit allocation amount nets credit against the invoice through canonical settlement; refund remains separate. Rejected automatic amount derivation and implicit cash movement.
