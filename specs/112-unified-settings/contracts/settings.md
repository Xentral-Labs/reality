# Existing API and UI Contracts
- GET `/api/auth/me`: signed-in AuthUser; read-only recovery.
- PUT `/api/auth/profile`: display_name(max150, trimmed), language(en/de/nl/es), locale(en-GB/de-DE/nl-NL/es-ES), timezone(valid IANA). Explicit account save only.
- GET `/api/tenants/{tenant}/settings/members`: owner-only; members/invitations max500 each; canonical invitation expiry maintenance retained.
- GET `/api/tenants/{tenant}/settings/ai`: owner summary; use nested copilot.available/credential_mode/model. No connectivity claim or rendering fingerprints/token metadata.
- `/app/settings?tenant={id}&settings_view=personal|access|ai`: unknown view falls back to personal. Drafts never serialized.
- `reality:theme-changed`: local preference updated; consumers reread existing theme storage.

Access summary retains the canonical pending/expired invitation filter. Delivery states are pending, processing, delivered, retry and failed; labels are localized and distinct from the invitation state.
