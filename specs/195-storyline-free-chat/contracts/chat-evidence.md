# Chat Evidence
GET /api/tenants/{tenant_id}/storyline/chat/{message_id} is owner-scoped and read-only.
Returns available, items, has_more. Unknown/foreign/non-assistant message is 404.
An existing assistant message without retained attribution returns available=false.
Items are exact recorded calls and proposal-linked decisions in ordinal order;
internal chat.reply rows are excluded. No arbitrary trace IDs accepted from clients.
