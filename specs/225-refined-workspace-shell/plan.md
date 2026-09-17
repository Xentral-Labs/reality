# Implementation Plan: Refined workspace shell

## Summary
Implement approved spec225 as a web-adapter-only change. Keep the same mounted
components and service paths; rearrange shell chrome and consolidate its CSS.

## Technical Context
React/TypeScript, Tailwind/CSS, Lucide, native popovers, Node contract tests and
Playwright fixture browsers. No dependencies, backend changes or migrations.

## Constitution Check
| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | No business reads or provenance changed |
| Reality authority | PASS | No document state or derived authority introduced |
| Proven schema | PASS | No persistence changes |
| Tenant/service boundary | PASS | Existing service callers and keyed chat reused |
| Specification/test evidence | PASS | Approved concept, test-first browser checks |
| Explainable web | PASS | Descriptions disclosed; existing evidence links unchanged |
| Simplicity/storage discipline | PASS | Existing components, CSS and native popovers |
| Received values | PASS | No calculations or source-value edits |

Pre-design and post-design results are PASS; no exceptions.

## Design and repository paths
- `apps/web/src/unified/Shell.tsx`: sidebar owns company block/utilities; one content
  header with description disclosure and neutral chat control. CSS grid positions
  mounted content and chat without remounting. Mobile remains a labeled drawer.
- `CompanySwitcher.tsx`: compact rail initial, dynamic popover anchor, existing menu.
- `ActionLauncher.tsx`: sidebar placement, native popover escapes scroll
  clipping; existing discovery, confirmation and form dispatch retained.
- `ProfileMenu.tsx`: appearance control passed from existing shell preference logic.
- `ChatPage.tsx`: 48px dock header and optional close control, existing history/new chat.
- `apps/web/src/tailwind.css`: replace obsolete header rules; local neutral shell
  palette, sizing, responsive grid and touch behavior. Preserve unrelated CSS.
- `apps/web/scripts/refined-shell-browser.mjs`: acceptance fixture for new layout,
  menu reachability, themes/languages, drafts, company switching and screenshots.
- Existing shell/navigation/simulation/title browser and contract expectations:
  update only superseded placement/geometry assumptions, preserving functional checks.
- `docs/WEB_SPEC.md`: authoritative placement update.

## Tests before implementation
Add acceptance browser checks first; observe old header/placement failure. Retain
existing contract suite and run navigation, simulation and title-count regressions.
Required gates: `make spec-check`, `make lint`, `make web-build`,
`make docs-catalog-check`; relevant fixture browsers and visual screenshots. Backend
and migration checks follow the repository CI changed-path gate: no backend-affecting
paths changed, so they are not required for this feature. An additional backend run
was attempted for broader confidence; its partial result and isolated timeout recheck
are recorded separately, without claiming a complete backend pass. On this host use
`gmake`, because the system `make` is blocked by the Xcode license prompt.

## Layer order
Domain → services → tools: no changes needed. Implement web adapter only.

## Migration and rollback
No migration. Revert feature changes to restore chrome. Existing navigation and theme
storage keys remain; no business data is written by layout changes.

## Review risks
Scroll-container menu clipping, desktop sticky alignment, mobile dismissal, rail
company access, dynamic title/count portals, standalone Chat height and stale
company overlays. Acceptance tests target these directly.

## Activities consolidation follow-up
Rename inspectorSections labels with all supported translations; remove only the
Shell ActivityDrawer import, local state/effect, trigger and mounted instance. The
timeline API, ActivityDrawer, HomePulse, ActivityGraph, FlightRecorder and projection
inspection share this read path and remain. Constitution Check: PASS; no data, service
or authorization changes. Add navigation and shell assertions before implementation;
move shared drawer regression entry to Home. Run the existing required frontend gates
and both shell/activity browsers. No critical analysis findings or unresolved scope.

## Action translation regression plan
Review: scope is restoration of FR-007, without unresolved clarification. Constitution
Check passes: translated interface labels only, no source values or service changes.
Before implementation, test every executable discovery category/group/entry label
against the three non-English dictionaries and observe the five missing labels.
Add translations, run that regression and the required frontend gates, and extend the
existing shell browser to assert translated shipping labels and German menu search.

## Command palette presentation plan
Scope review: the user requests presentation and shortcut access only; no unresolved
clarifications. Constitution Check PASS: existing discovery and execution paths stay
unchanged. T016–T018 cover FR-009. Move ActionLauncher into the company block, replace
its visible Actions label with search and a shortcut hint, center its native popover,
and focus/reset search on open. Register and clean up one shortcut listener per keyed
launcher; respect existing modal dialogs. Preserve native Escape/focus behavior.
Extend shell browser before implementation for keyboard opening, focus, centering,
query reset, absence of a lower launcher and all existing localized entries. Run
required frontend gates, shell browser and launcher discovery regression.

## Quiet shell boundaries plan
Owner approved FR-010 explicitly. Constitution Check PASS; no unresolved questions.
Remove four CSS border declarations only. Preserve chat dock border-left and active
tab border. Existing shell browser checks responsive geometry, themes and keyboard
behavior; visually review screenshots. Run required frontend gates. No additional
unit tests for this reversible CSS-only change.

## Sidebar head grouping plan
Approved FR-011; no unresolved clarification. Constitution Check PASS. Move the logo
inside CompanySwitcher and move the existing collapse control into the head row.
Collapsed rail stacks switcher/toggle without overflow. Restyle the palette trigger
as a compact field; keep its explicit Search actions accessible label. Remove the
visible Daily work label while retaining the landmark. Update superseded placement
contracts and existing navigation browser assertions first; run frontend gates and
shell/collapsible navigation browsers, then inspect desktop/mobile/rail screenshots.
No business service changes or new dependencies.

## Unified tab header plan
Approved FR-012. Constitution Check PASS; no unresolved clarification or backend scope.
RegisterHeader reports whether it renders multiple direct tab controls through a
shared layout context and provides an adjacent active-tab count portal target. Shell
hosts existing tab/action portals in its header; a visually hidden heading preserves
page orientation for assistive technology on tabbed pages. Single-title pages retain
the visible title/count. Keep the tab portal stable to avoid remounting controls.
Scrollable tabs and compact mobile action/chat controls prevent overflow; action menus
must remain outside tab overflow. Tests first update header placement expectations,
then run full frontend gates, shell, page-introduction and title-count browsers covering
routes, filters, empty/error/loading counts, mobile geometry and existing page actions.

## Commitments header regression plan
Restore FR-012 on the legacy Commitments strip. Constitution Check PASS; no unresolved
clarification. Update daily-work browser to locate direction tabs/counts in the shell
header before wrapping the existing tabs in RegisterHeader. Preserve labels, counts,
side switching/reload and list behavior. Run frontend gates and the daily-work browser
matrix; verify header/body placement and screenshots. No backend changes required.

## Inbox consolidation plan
Approved FR-013. Constitution Check PASS; no unresolved scope. Reuse dailyWork's three
canonical selections and add a pure selection predicate for Inbox membership. Shell
renders one Inbox destination and one shared RegisterHeader for its three tabs.
RegisterHeader gains an explicit local placement for subordinate direction/rule controls;
these do not register header/count targets. Existing queue components/services remain.
Tests first cover Inbox route membership (including nested rules and excluding Sales),
then adapt daily-work browser for primary tabs, local side selection and one sidebar
entry. Run frontend gates, daily-work and page-header/count browsers. No schema changes.

## Empty chat history plan
Approved FR-014. Constitution Check PASS. ChatPage reports successful history availability
to CompanyChatPage; its tenant-scoped initial snapshot controls automatic desktop column
visibility, while current availability controls the history button. Keep portal targets
mounted inside a hidden column so ChatPage/composer do not remount. Move New chat to the
conversation toolbar. Include archived history; do not settle initial state on errors.
Plan browser checks for empty layout, first-session stability, explicit opening/closing,
revisit, archived-only history, mobile and tenant change. Run required frontend gates.
