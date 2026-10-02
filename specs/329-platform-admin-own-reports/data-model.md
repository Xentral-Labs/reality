# Data Model

No schema change. AppUser.id/status/is_platform_admin is authoritative current account state. TenantMembership remains the actual active company role. Tenant.id/purpose/archived_at bounds administrator fallback to accessible business companies. AnalyticsReport.owner_user_id and AnalysisRequest.requested_by_user_id remain mandatory private ownership filters. ChangeProposal sealed author binding is unchanged. No membership is created by administrator analytics access.
