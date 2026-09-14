# Research
Plan research agent audited existing services, auth and UI. No external research needed for repository-local contracts.
- Decision: reuse existing company create and member methods. No rename API exists; retain read-only identity. Alternative rejected: inventing a new settings backend.
- Decision: resend pending or expired invitations, matching memberships.resend_invitation; revoke pending only. Backend enforces cooldown, rolling limits, normalized duplicate neutrality and owner authorization.
- Decision: use explicit read recovery after unknown writes, never replay automatically or identify a company by display name. Existing create tenant/membership transaction gap remains a documented backend limitation.
- Decision: pass accepted company ID in destination URL; localStorage alone is not consumed by unified selection.
- Decision: stateful intercepted browser fixtures avoid real email; existing PostgreSQL suites prove service and HTTP permissions.
