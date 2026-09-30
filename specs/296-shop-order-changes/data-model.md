# Data Model: Shop Order Changes and Refunds

No new table and no new column. Everything is recorded with existing records.

| Need | Record | How |
|---|---|---|
| A later order version | `source_record` | as today: new version, supersedes link, lossless payload |
| An applied reduction | `commitment_revision` / `commitment.status = cancelled` | existing services with `source_record_id` = the version |
| Why a version waits | `interpretation_outcome` | `needs_review`, `reason_code` (single code or `shopify_changes_require_review`), summary naming each code and line |
| A refund | `source_record` (`shopify` / `refund` / refund id) | split from the order payload; its own import job |
| Refund evidence | `document` (type `sales_refund`) + `document_line` | amount and currency as stated; one line per refunded position with `source_line_id` = the Shopify line it refunds; no ledger entry |
| Expected return after a refund | `return_announcement` | `source_record_id` = refund source, reference `Refund <id>` |
| An unknown item | `document_line` with `item_id` NULL | stated SKU kept in `sku` and `payload`; no commitment until assigned |
| Item assigned by a person | `document_line.item_id`, new `commitment` | through the reviewed tool; event `document_line.item_assigned` |

## Document type `sales_refund`

Evidence of money the shop returned to a customer. Not a settlement document: no control
account, not an open item, not a credit note. Its lines name the Shopify line they refund through
`source_line_id`, and the refund's source payload names the order. They deliberately do not set
`billed_document_line_id`: every billing and crediting reader counts lines carrying it, and some
(for example `exceptions._billing_lines`) do not filter by document type.

## Events

| Event | Subject | Payload |
|---|---|---|
| `commitment.revised`, `commitment.cancelled` | commitment | unchanged; `source_record_id` = the version |
| `document.recorded` | document | for `sales_refund` |
| `return.announced` | return_announcement | unchanged |
| `document_line.item_assigned` | document_line | item id, created commitment id |
