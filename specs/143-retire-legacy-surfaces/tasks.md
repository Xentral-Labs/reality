# Tasks: Retire legacy browser surfaces

## Setup and analysis
- [x] T001 Review dependencies and accepted removal scope in specs/143-retire-legacy-surfaces/spec.md and research.md.
- [x] T002 Pass Constitution and requirement coverage review in specs/143-retire-legacy-surfaces/plan.md.

## US1 — Sole app and bookmarks
- [x] T003 [US1] Add failing executable route tests in apps/web/scripts/entry-routing.test.mjs (FR-001/002/005).
- [x] T004 [US1] Implement apps/web/src/entryRouting.ts and sole App.tsx/Auth.tsx entry (FR-001/002/005).

## US2 — Playground retirement
- [x] T005 [US2] Cover old entry/run and malicious account-return paths in apps/web/scripts/entry-routing.test.mjs (FR-003/005).
- [x] T006 [US2] Remove apps/web/src/playground and legacy presentation after extracting shared ExceptionCatalog into unified/ (FR-003/004/005).

## US3 — Distribution and acceptance
- [x] T007 [US3] Replace obsolete presentation contracts, remove orphan CSS/client code and update apps/web/package.json (FR-005/006).
- [x] T008 [US3] Update current build/docs/site links and docs/WEB_SPEC.md retirement contract (FR-006).
- [x] T009 [US3] Add and run apps/web/scripts/retirement-browser.mjs plus retained frontend and backend gates (FR-001–006).
- [x] T010 Review final diff and record verification in specs/143-retire-legacy-surfaces/quickstart.md.
- [x] T011 Publish the verified change as [PR #153](https://github.com/Xentral-Labs/reality/pull/153).

## Dependencies and strategy
T001→T002→tests T003/T005→implementation T004/T006→T007/T008→T009→T010. No new domain/service work. Independent docs reads may run alongside dependency reads; changes are applied sequentially to avoid deleting shared code. Each user story has the independent acceptance scenarios in spec.md.

## Profile menu follow-up
- [x] T012 Add profile navigation, external-link and failed/successful logout scenarios to apps/web/scripts/retirement-browser.mjs (FR-007).
- [x] T013 Add apps/web/src/unified/ProfileMenu.tsx and wire the bottom Shell account entry from UnifiedApp (FR-007).
- [x] T014 Run browser, localization, format/build checks and update the PR and local Docker web image (FR-007).

- [x] T015 Separate personal/company settings navigation and header in SettingsPage.tsx, Shell.tsx and routing.ts; verify routing and browser entry/reload (FR-008).

- [x] T016 Add company list, current marker, switch/reload and separated creation browser scenarios (FR-009).
- [x] T017 Wire authorized company list and existing switch context; separate creation area (FR-009).
- [x] T018 Verify frontend gates/browser, refresh Docker web and update PR evidence (FR-009).

- [x] T019 Move company creation to the top action and shared-style modal; verify dismissal/focus and retained gates (FR-009 clarification).

- [x] T020 Replace cross-company navigation with focused owner-management dialogs, preserve working company, verify request scope and update evidence (FR-011).

- [x] T021 Align the Home CTA with commitment terminology and verify localized production build; no behavior change.

- [x] T022 Align commitment list/search/links and clarify customer-delivery scope; verify existing frontend checks and publish updated web image.

- [x] T023 Add initial selection regression scenarios, implement one-time automatic selection with replace history, verify browser/frontend gates and refresh local Docker (FR-012).

- [x] T024 Replace duplicate work entry with register/detail flow, add regression coverage, verify frontend/browser and refresh/publish (FR-013).

- [x] T025 Add a unified-shell contract for the canonical `Reality` product wordmark (FR-014).
- [x] T026 Capitalize the visible unified-shell wordmark without changing technical identifiers (FR-014).
- [x] T027 Run the focused frontend contract, formatting, production build and spec checks (FR-014).
