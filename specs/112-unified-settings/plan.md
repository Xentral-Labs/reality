# Implementation Plan: Unified Settings

## Architecture
Adapter-only increment. Existing domain → services → API remain unchanged. Add `apps/web/src/unified/SettingsPage.tsx`, extend `routing.ts`, `Shell.tsx`, `UnifiedApp.tsx` and pass AuthGate updateUser from `App.tsx`. Use controlled profile draft and a submitted snapshot with explicit saving/uncertain/recovery state. Definite API4xx can retry explicitly; network/5xx can only read back before another write. Compare normalized submitted fields with api.me; call updateUser after authoritative successful reads/writes. Keep profile edits out of URL/storage.

Use grouped inner navigation and one focused form/detail panel. Mount owner-only child reads only when `company.role === owner`. Existing useRead handles cancellation on company/view change. Display members/invitations without claiming completeness; show up-to500 limit. AI projection renders nested copilot availability/mode/model only, never hardcoded provider_name. Links to `/app/companies?tenant=...` lead to supporting advanced settings.

Theme preference uses existing local storage and applyTheme. Emit a shared theme-change event from storeThemePreference. Header and settings subscribe; header watches OS changes and applies current preference. Cleanup all listeners. No new dependencies.

## Constitution Check
| Principle | Result | Evidence |
| --- | --- | --- |
| Source → Evidence → Reality | PASS | No business records change; settings are account/configuration authorities. |
| Operational authority and shortest links | PASS | No status derivation or relationship added. |
| Proven schema | PASS | No schema or backend changes. |
| Tenant/service boundaries | PASS | Existing authenticated profile and scoped owner APIs. |
| Specification and tests first | PASS | Route/browser failing proof before implementation. |
| English artifacts | PASS | All artifacts/code English; UI four locales. |

## Research and test plan
Research delegated under speckit-plan to finance_read_audit: verified profile validation, AuthGate callback, unequal admin bypasses, membership500 bound/expiry, AI nested configuration and theme event gap. See research.md.

First add route contract and browser tests. Prove profile save payload and exactly-one PUT, reload/localization, validation rejection, ambiguous applied/not-applied recovery, retry, owner/member guard, company isolation, local theme/header/OS behavior, keyboard labels and48 screenshots. Existing PostgreSQL tests test_user_access and test_master_data_api cover backend authority. Run full Python suite, web contracts/i18n/build/format, all unified browser scripts, docs tests/build/format, repository spec/lint gates. Inspect representative screenshots and authenticated synthetic preview.

## Rollback
Remove new route and restore supporting settings link; existing profile APIs/data remain valid. Feature flag still gates the whole new App. No data rollback or migration. Legacy retirement remains an explicit future rollout decision.

Access summary retains the canonical pending/expired invitation filter. Delivery states are pending, processing, delivered, retry and failed; labels are localized and distinct from the invitation state.
