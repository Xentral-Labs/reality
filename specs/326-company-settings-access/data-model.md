# Data Model
No schema changes. TenantMembership.role/status and AppUser.status remain the authority for private author access. Missing TenantSummary.role denotes no active membership. MCP_URL/API_URL remain configuration, not business data. Report ownership stays tenant_id + owner_user_id. No stored credentials, permissions or reports are changed by this correction.
