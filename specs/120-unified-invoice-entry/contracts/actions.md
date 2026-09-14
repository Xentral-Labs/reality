# Contracts
Common delivery-actions prepare accepts sales_invoice_record and supplier_invoice_record.
Intent: order_line_id, quantity, gross_amount, number, optional effective_at (UTC ISO timestamp).
Review: intent, relevant order/line/reference state, effect and token. Existing proposal endpoints
review, approve, reject, detail and reconcile retain current access and explicit confirmation.
Receipt retains canonical records list. Verified links expose source, invoice, line and postings.
Order selection uses existing paginated evidence document search plus tenant-scoped Inspector.
