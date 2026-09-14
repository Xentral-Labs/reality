# Plan: Unified company access
**Language**: English
## Technical Context
React/TypeScript shared API client, existing PostgreSQL membership and auth services. No new dependency, schema or public endpoint.
## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Provenance and Reality | Account settings do not alter operational records or authorities | PASS |
| Schema | Reuse Tenant, TenantMembership, CompanyInvitation and InvitationDelivery | PASS |
| Tenant/services | Existing owner-scoped methods; no adapter business writes | PASS |
| Test-first | Stateful browser scenarios before UI; existing auth/service regression suite | PASS |
| Explainability | Explicit target company/email, role and separate delivery status | PASS |
| Received values | No recalculated business values | PASS |
| Simplicity | Small Settings components; existing shared API and AuthGate | PASS |
## Design
Add CompanySettings.tsx for identity and CreateCompany with name review. Add MemberAccess.tsx replacing read-only summary, preserving 500-row bounds and statuses. Shared local action state handles review, cancellation, busy lock, rejected/unknown result and explicit read recovery. Keep writes in api.ts existing methods.
Extend Settings routing with company section, shell entry, and useCompanyContext bootstrap refresh with selected opaque ID. Zero-company fallback uses same CreateCompany. Auth acceptance includes returned company ID in URL.
No domain/service/tool changes; implement adapters only because lower layers already exist.
## Verification
First write apps/web/scripts/unified-company-access-browser.mjs with intercepted HTTP and observe missing UI failure. Cover no-company/create, cancel/double submit, queued versus delivered, resend/expired, revoke/remove, owner/member, company switch, duplicate names, 4xx, unknown response and failed recovery, invitation acceptance tenant, mobile/dark. Reuse existing settings browser. Run full backend suite, web build/contracts/i18n/format, root lint/spec/diff checks. Inspect screenshots.
## Risks and Rollback
Do not send real mail or create shared companies. API company creation currently commits tenant before owner membership: existing limitation, do not infer success from name or automatically replay on unknown result. Bootstrap may fail after successful create; retain returned ID for recovery. Existing archive/delete remains supporting administration. Revert UI increment without database migration. No unresolved Constitution exception.
