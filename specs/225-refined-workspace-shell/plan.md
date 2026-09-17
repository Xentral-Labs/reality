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
