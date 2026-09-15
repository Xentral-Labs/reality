# Chat Evidence
GET /api/tenants/{tenant_id}/storyline/chat/{message_id} is owner-scoped and read-only.
Returns available, items, has_more. Unknown/foreign/non-assistant message is 404.
An existing assistant message without retained attribution returns available=false.
Items are exact recorded calls and proposal-linked decisions in ordinal order;
internal chat.reply rows are excluded. No arbitrary trace IDs accepted from clients.

Independent entry: GET /api/storyline/free-play returns available=false without
creation, or available=true plus the existing CompanySetupResult. POST accepts only
strict confirmed and delegates canonical Sandbox creation/replay. Archived receipts
stay archived; ordinary-company collisions are conflicts. Evidence reads include the
designated standalone practice run, while chapter APIs remain Storyline-only.
