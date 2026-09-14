# Processing Contract

The existing source intake and import-work HTTP endpoints remain unchanged.
Changed Shopify order payloads are accepted and retained. Processing returns no new
interpretation; coverage shows needs_review and an explicit unsupported-update reason.
ImportJob is completed because processing reached a deliberate review decision, not
because the source produced business Reality. No retry is scheduled automatically.

Existing service and agent coverage reads expose the same outcome. HTTP import-job
reads expose the same safe review reason in the existing error field.
The synchronous ingest_shopify_order helper raises InvalidOperation with the review
explanation after retaining the source/outcome. Stale deliveries retain their existing
error message. No mutation permission or confirmation contract changes.
