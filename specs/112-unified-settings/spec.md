# Feature Specification: Unified Settings

**Created**: 2026-09-07
**Status**: Owner-authorized continuation of the accepted unified App migration.
**Language**: English

## Context and Intent
### Problem
Settings currently leave the coherent App and personal preferences are hidden in a separate profile page.
### Scope
One grouped Settings destination with personal preferences, company access and AI configuration summaries, using existing account and company authorities.
### Non-Goals
No business action, invitation sending, member changes, credential/token editing, connectivity probe, company lifecycle, schema, deployment, merge or legacy/Playground retirement. Advanced setup remains reachable in supporting company settings.

## User Scenarios & Testing
### US1 — Make the App personal (P1)
Save display name, language, number/date locale and IANA timezone explicitly. Settings apply across the account immediately and survive reload. Choose light, dark or system appearance for this browser; header and settings stay synchronized, including an OS change while system is selected.
Acceptance: language and locale remain independent; an existing valid timezone outside common presets is preserved. Invalid timezone retains the draft. A lost save response never causes an automatic second write; checking current preferences reconciles the attempted values or explains the difference.
### US2 — Understand access (P2)
An owner opens Company access for the selected company, sees its members and invitation states, and can continue to supporting company administration. A member sees an owner-access explanation without requesting the owner-only endpoint.
Acceptance: switching companies clears prior details; failed reads offer Retry. Lists are bounded at 500 members and 500 invitations and are not presented as complete company totals.
### US3 — Understand AI setup (P2)
An owner sees whether credentials are configured, managed or company-owned, and the configured company model. This is configuration presence, not a connectivity health claim. Advanced setup remains a supporting link.
Acceptance: member view makes no owner-settings read; no key, fingerprint, token prefix or endpoint URL appears in the summary.

## Requirements
- **FR-001**: `/app/settings` belongs to the unified shell with bookmarkable personal/access/AI sections and a selected sidebar entry. Unknown section falls back to personal; company switch retains the section and resets company data.
- **FR-002**: Personal form explicitly saves the four existing profile fields once through the existing authenticated API and updates application localization from the returned user. Show account-wide scope, required timezone and max150 display-name limit.
- **FR-003**: Disable duplicate writes while saving or outcome is uncertain. Definite client rejection retains the editable draft. Network/5xx ambiguity requires read-only profile recovery; only an authoritative match confirms success. A mismatch preserves the draft and allows a new explicit save. Recovery failure stays uncertain. No automatic replay.
- **FR-004**: Light/dark/system appearance is browser-local and synchronized with the header and OS system preference.
- **FR-005**: Access summary uses the existing owner membership API for the current company, reports bounded members/invitations and their separate states, and supports empty/error/retry states. Non-owner UI does not request this API.
- **FR-006**: AI summary uses the existing owner settings API and exposes only credential availability/mode and configured company model. Availability is not live connectivity. Non-owners do not request it; no secret metadata is rendered.
- **FR-007**: All copy is localized in en/de/nl/es; forms are keyboard usable and layout works at390/1440px in light/dark. Supporting company administration links preserve the opaque tenant ID.

## Success Criteria
Browser tests prove explicit profile save/reload, immediate language change, recovery without duplicate PUT, role isolation, company reset, theme synchronization and 48 section/locale/theme/viewport combinations. Existing backend and App regression gates stay green.

## Assumptions and Dependencies
The user repeatedly authorized continuing the accepted navigation and migration. Existing authenticated profile validation, owner access APIs and their role rules remain authoritative. Profile preferences are account-scoped; appearance is browser-local. The existing membership GET may expire elapsed invitations through its canonical service. Platform-admin bypass differs between APIs; this UI conservatively shows summaries only to active company owners, without changing backend permissions. Owner review of final rollout and retirement remains separate.

## Requirement Traceability

| Requirements | Stories | Planned evidence |
| --- | --- | --- |
| FR-001 | US1–US3 | Route/section roundtrip and browser company reset |
| FR-002 FR-003 | US1 | Profile payload, reload, validation and uncertain-result recovery |
| FR-004 | US1 | Local theme/header/system synchronization |
| FR-005 FR-006 | US2 US3 | Owner/member request isolation, retries, empty states and safe AI projection |
| FR-007 | US1–US3 | Four locales, two themes, two widths and keyboard save |
