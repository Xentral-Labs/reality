# Order action contract

Existing delivery-actions prepare accepts `order_create` with request_id and canonical
manual-order arguments. Review includes exact intent, normalized document/lines and
current reference labels. Approval requires confirmed=true and current review_token.
Detail/reconcile share existing lifecycle. Receipt is source_record_id, document_id,
ordered document_line_ids and commitment_ids. Execution is atomic; reconciliation
never calls order_create. Human number is not an idempotency key. Richer supported
intent survives Edit; unsupported fields fail visibly before preparation.
