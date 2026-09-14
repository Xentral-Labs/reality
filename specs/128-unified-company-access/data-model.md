# Data model
No schema changes. Tenant identity is opaque; names are non-unique. TenantMembership identifies access and role. CompanyInvitation and InvitationDelivery separately identify acceptance and transport state. Services remain authoritative for transition guards, expiration, rate limits and recipient matching. UI retains only drafts, review targets and uncertain request state.
