# Plan: Unified AI and MCP access
## Technical Context
React/TypeScript frontend-only; existing aiSettings/saveAISettings/createMCPToken/revokeMCPToken APIs and owner gates. Existing Python services, vault and MCP authorization unchanged. No dependencies or schema changes.
## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Source / Reality / received values | Configuration only; no new operational records or derived authority | PASS |
| Schema / simplicity | Existing records and endpoints | PASS |
| Tenant / service | Existing owner/service authority; company-keyed component lifetime | PASS |
| Explainability | Managed vs Anthropic runtime capability explicit; no live-connection claim | PASS |
| Test-first | Browser test red before component; full existing backend checks | PASS |
| Secret boundary | Password input/in-memory key only; sanitized review and persisted marker; one-time token | PASS |
## Design
AISettings.tsx replaces AIStatus inside SettingsPage.tsx and the old advanced-company link. A compact current summary precedes a managed/company-Anthropic form. Anthropic model/base URL are fixed server metadata, not editable. Unsupported stored provider configuration is readable with an explicit warning; switching requires a fresh key and review. Managed review explicitly revokes the stored company credential. Saving never triggers a remote call.
MCPAccess.tsx renders in an advanced details section. It uses the returned catalog to select exact nonempty tool names (default none) and labels read/propose/confirm accurately; no new wildcard granting. Existing token IDs/prefixes/scopes are inspectable with 25-row paging, tools with search and bounded display. New secret exists only in mounted component state and can be copied/hidden. Revocation identifies ID/name/prefix.
Shared AISettings owner component owns single-flight review, writes and a sessionStorage unresolved marker containing random attempt ID and action kind only. No credentials, token values or payloads in persistence. Mark before request; clear submitted key state; compare marker IDs before removal. Reload requires explicit GET recovery. Read results describe current state, not receipt attribution. Lost token response permits explicit inspection/revocation, never secret reconstruction or automatic re-creation. Unmount/tenant lifetime guards ignore late responses and clear visible secrets.
Existing read may initialize settings or migrate an old vault entry internally; it does not issue a provider save or token create/revoke. Do not call it strictly storage-write-free.
## Verification
New stateful HTTP browser proves provider effects/review/cancel, fixed model, unsupported presets, exact tool permissions, one-time secret/copy failure, token revoke, unknown save/create/revoke, reload/read failure, duplicate names, member gate, company switch and four-language responsive light/dark views. Existing settings browser updated only for full configuration fixture shape; original secret-exclusion assertions preserved. Full backend suite, web contracts/i18n/audit/build/format, lint/spec/diff required. No real shared secrets or external network provider calls.
## Rollback and limitations
Frontend rollback restores summary/old link; existing records remain compatible. No action idempotency receipt, no token expiry, no live connectivity test, and current non-Anthropic runtime support remains a separate backend feature. Lists currently come from an unpaginated settings API; display paging does not claim server-side pagination.
