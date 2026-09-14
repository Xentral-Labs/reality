# Research decisions

- Reuse existing finance GETs and types; avoid a second read service. Reviewed with delegated read-only research under speckit-plan.
- Open items use projection_page/projection_totals, not legacy open_item_page; filtering and totals precede paging. Default to receivable/outstanding and expose payable explicitly.
- Payment search matches IDs, but its aggregate search matches full projection payload. Do not render payment aggregate headlines. Recorded reversal rows are history, not cash balance.
- Journal row and control filters agree. No date inputs added because existing adapter does not validate arbitrary date strings.
- Open-item Inspector uses document ID; payment uses cash-entry ID; journal uses ledger-entry ID. No invoice-to-delivery relationship inferred.
- Existing GETs may refresh derived projection caches; no authoritative business effects arise from investigation.
- No external technical dependency research required; implementation uses installed code and existing contracts.
