# HTTP Contract: Conditional Chat Session Removal

## Copilot session projection

Each item in `GET /api/tenants/{tenant_id}/copilot` includes:

- `message_count`: non-negative integer derived from tenant-owned durable Chat Messages.

The field describes current state for presentation; it does not authorize deletion.

## Remove session

`DELETE /api/tenants/{tenant_id}/copilot/sessions/{session_id}` retains status `204`.

- If the tenant-owned session has zero messages at mutation time, it is permanently deleted.
- If it has one or more messages, it is archived and remains restorable.
- Unknown or foreign-tenant IDs return the existing not-found response.
- No Change Proposal or business Reality record changes.
