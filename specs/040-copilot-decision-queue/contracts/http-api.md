# HTTP Contract

- `GET /api/tenants/{tenant_id}/change-proposals?status=pending|history` returns tenant-scoped
  proposal summaries with parsed input and output.
- `DELETE /api/tenants/{tenant_id}/copilot/sessions/{session_id}` archives the session and returns
  204 without deleting messages or proposals.
- `POST /api/tenants/{tenant_id}/copilot/sessions/{session_id}/restore` restores the session.
- `GET /api/tenants/{tenant_id}/copilot?archived=true` lists archived sessions; the ordinary
  request lists active sessions.
- Copilot payload contains proposal cards only when an active session exists.
