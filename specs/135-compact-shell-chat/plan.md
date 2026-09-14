# Plan
## Constitution Check
PASS: all eight principles. Presentation-only composition on existing services; no schema, database writes, source/value derivation or authorization changes. Tenant-keyed chat state; existing explicit action confirmations remain.
## Design
Shell owns dock visibility, preserves its mounted ChatPage while hidden, and renders a responsive right column. Existing copilot route uses HomePage behind the dock. DeliveryCase opens the same dock via a presentation event; current selected delivery remains its context. Add dock rendering mode to ChatPage with bounded height and a compact conversation header. Use unique composer IDs for contextual dialogs. Main viewport and sidebar scroll below the sticky 56px header. Place the Analytics section before Company, with Reports as its first destination; remove migration support links under FR-008.
## Tests and order
Write browser proof first and observe failure on missing dock. Implement Shell, UnifiedApp and ChatPage; add localized labels. Verify browser geometry, navigation/draft/company behavior, existing app/delivery/activity regressions, contracts/i18n/build/format and spec/lint/diff gates. No core changes; existing Spec134 full backend baseline remains applicable.
## Rollback
Revert shell composition and dock mode; no data migration or server restart.

## Navigation correction
The owner clarified FR-004: move Analytics out of Company into its own section before Company, with one Reports link. Constitution PASS; presentation only. Update the existing shell browser hierarchy assertions before editing Shell.tsx. Verify the 48-layout shell browser matrix, build, formatting, localization audit and spec policy. No service or schema changes; rollback is the navigation markup.

## Company selector refinement
FR-006 Constitution PASS: presentation only, existing tenant callback, no new authority or schema. Extract CompanySwitcher.tsx into Shell. Use a native non-modal popover with normal buttons and browser light-dismiss/Escape focus behavior. Show company initials, name, practice label, selected state and duplicate IDs. Update browser selectors and add dismissal/selection assertions before implementation. Verify shell matrix, settings/company-access browser regressions, frontend contracts, build, i18n, formatting and spec gates.

FR-007: explicit owner-approved navigation simplification; Constitution PASS. Remove the sidebar item and its unreachable click branch. Update shell navigation assertions and existing chat-entry browser interactions. Verify shell browser, unified app/delivery browser, build and spec/diff gates. No API or chat behavior change.

FR-008 Constitution PASS: owner explicitly authorized all audited exit removals. Remove anchors in Shell and register/detail pages; replace sandbox exit with read-only explanation and live-company switches, route unsupported chat proposals to Decisions, display unsupported decision notice, and keep role-less receipts in Inspector search. Existing service and data boundaries unchanged. Update regression contracts before implementation; verify frontend contracts, build, localization and shell/application browser fixtures.
