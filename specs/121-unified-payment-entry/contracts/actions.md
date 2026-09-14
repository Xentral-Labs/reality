# Contracts
Common prepare accepts customer_payment_post and supplier_payment_post.
Intent: invoice_id, amount, optional payment_number/effective_at/source_record_id.
Review contains exact intent, invoice/control/source/allocation snapshots, currency/party,
open-before and open-after plus token. Existing approve requires token and explicit confirmation.
Receipt remains {records: [two ledger_entry references]}; detail adds payment document,
allocation, invoice and optional original-source links. Unknown recovery never invokes mutation.
Current observation contains invoice open amount and whether the recorded allocation is active.
Invoice choices reuse tenant-scoped paginated open-items reads.
