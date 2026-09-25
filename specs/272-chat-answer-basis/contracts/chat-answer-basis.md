# Chat Answer Basis Contract

`GET /api/tenants/{tenant_id}/storyline/chat/{message_id}` remains tenant-scoped and read-only.

The response retains `available`, `items`, and `has_more` for the legacy Storyline trace. It adds `basis` with `available`, zero to four compact `rows`, `additional_count`, `calls`, and `has_more`. Each row supplies `label`, `value`, `role`, and optional `record_type`/`record_id`.

Unknown, foreign-tenant, and non-assistant messages return 404. Historical messages return `basis.available=false`. Missing Storyline eligibility no longer prevents a valid assistant message from returning its basis. The client hides the disclosure when both basis and legacy items are unavailable.
