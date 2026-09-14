# Unified AI provider and MCP access settings
**Language**: English
**Created**: 2026-09-08
**Status**: Accepted within the owner-approved next migration step
**Input**: Owner approved continuing with AI setup after the remaining-scope review.

## Context and Intent
### Problem
The new settings page only summarizes AI configuration and links owners back to the old company administration for provider credentials and external agent access.
### Scope
Owner-only provider configuration and reviewed MCP token creation/revocation in unified Settings. Preserve existing service and authorization semantics while making credential effects and tool permissions explicit.
### Non-Goals
New AI providers/models, live provider testing, real credential changes during development, new MCP permissions, secret recovery, backend/schema changes and final legacy retirement.

## User Scenarios & Testing
### US1 — Configure Ask Reality (P1)
An owner opens current AI configuration, selects managed AI or a company Anthropic key and supplies a company key when required. Review shows the provider, model, endpoint and whether the key will be retained, replaced or revoked. Cancel makes no write. Saved status distinguishes configuration from connection health.
### US2 — Connect an external agent (P1)
An owner opens advanced MCP access, names a token and selects exact tools. The review distinguishes read, propose and approval/execution permission. A successful creation shows the secret once with copy/hide controls. Existing tokens show their IDs, prefixes and scopes and can be revoked after review.
### US3 — Recover an uncertain change (P1)
An interrupted response blocks new writes until an explicit current-state check. Reload preserves the unresolved marker without storing secrets. A lost token secret cannot be recovered; the owner can inspect active token IDs and revoke an unwanted token before replacing it. No automatic create/revoke/save retry occurs.
### Edge Cases
Missing or failed reads, member access, switching from an unsupported stored provider requiring a new key, managed mode revoking company credentials, non-catalog current model, empty tools, duplicate token names, rejected writes, double clicks, failed clipboard, lost response, refresh and company switch during a write.

## Requirements
- **FR-001**: Replace the old AI administration link with owner-only current configuration and a reviewed provider form; ordinary members must not request privileged configuration. Offer only the two modes used by the current chat runtime: managed and company Anthropic. Show the fixed server-provided Anthropic model/endpoint; other saved provider settings remain visible with an explicit runtime limitation.
- **FR-002**: Show exact provider/model/endpoint and key effect before saving. Existing Anthropic credentials may be retained or replaced; switching from another provider requires a new key. Managed mode explicitly revokes company credentials. Secrets remain write-only in memory, never in URL, browser persistence, review text or error messages. Clear submitted secrets and discard on company change/unmount.
- **FR-003**: Advanced MCP access shows endpoint and active token metadata; creating a named token requires an explicit nonempty tool selection. Default selection is empty. New UI grants exact tool names, never an implicit wildcard. Existing wildcard tokens remain visible and revocable. Review distinguishes read/propose/confirm and names each permitted tool.
- **FR-004**: Show a new token secret only from its successful creation response with explicit copy and hide; never persist it. Revocation reviews exact opaque ID, name and prefix. Cancellation and rereads create/revoke nothing. Clipboard failure leaves manual selection available.
- **FR-005**: Single-flight writes, tenant-bound lifetime guards and a persisted secret-free unresolved marker protect failed/lost responses and reload. Explicit current-state checks allow a new review but never claim an attributable receipt or recovered secret. Failed checks retain the block. Duplicate names are not identity.
- **FR-006**: Existing owner/tenant/practice and MCP authorization remain server-owned. Use existing services/API, no credentials sent to an external provider during setup verification and no new business records.
- **FR-007**: Four languages, keyboard review focus, responsive light/dark layout, bounded token/tool displays with search/paging and honest unavailable/error states. Existing personal and company settings remain functional.

## Assumptions and Dependencies
The existing API stores several provider presets but the current chat runtime uses company keys only for Anthropic and otherwise falls back to managed Anthropic credentials. This slice offers those two working modes, with a fixed server model/endpoint. Other saved presets remain visible and unchanged unless the owner explicitly reviews a switch. The API also supports a write-only company key and owner-scoped MCP tokens. Saving configuration does not verify a remote model. Managed mode depends on deployment credentials. No operation has an idempotency receipt; unknown outcomes use current-state inspection. Provider/capability authority remains in existing services. The owner's approval covers UI consolidation of these existing capabilities; no real shared credential mutation or external provider request is needed for implementation.

## Success Criteria
An owner can configure AI and create/revoke a scoped MCP token entirely in unified Settings. Review/cancel/reload do not silently mutate configuration. Clear credentials never enter persistent browser state. All requirements have passing existing backend and new browser evidence; required checks are green.

## Requirement Traceability
| Requirement | Tasks | Proof |
|---|---|---|
| FR-001/002 | T002/T003 | Provider review, key retain/replace/revoke, member gate and secret exclusion |
| FR-003/004 | T002/T004 | Explicit scopes, one-time token, revocation and clipboard behavior |
| FR-005 | T002/T005 | Unknown response/reload/read failure and in-flight company switch |
| FR-006 | T001/T002/T006 | Existing owner/vault/MCP backend suites and browser isolation |
| FR-007 | T004/T006 | Tool/token paging, four-language responsive screenshots and settings regressions |
