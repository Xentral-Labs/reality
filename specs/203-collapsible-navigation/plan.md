# Implementation Plan: Collapsible primary navigation

## Technical Context
React/TypeScript and existing Tailwind/CSS, no new dependencies. Presentation-only change.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | No record/answer changes | PASS |
| Reality owns operational state | Only local display preference | PASS |
| Proven schema only | No schema or migrations | PASS |
| Tenant/shared services | Existing navigation and service calls retained | PASS |
| Spec/test traceability | FR-001–004 covered by browser acceptance | PASS |
| Explainable web | All existing destinations remain reachable | PASS |
| Received values | No calculations or source changes | PASS |
| Smallest coherent design | Reuse links, CSS and browser preference; no second navigation | PASS |

## Design and Files
- apps/web/src/unified/Shell.tsx: local collapsed state with guarded localStorage read/write; desktop native toggle; explicit labels on existing links. Root data attribute controls layout. No remount of content/chat.
- apps/web/src/tailwind.css: desktop-only icon rail styling and body grid width. Global header preserves company selector beside the logo; header layout is independent of collapsed body width. Hide visual labels without removing accessible names. Existing mobile drawer unchanged.
- apps/web/src/unified/ProfileMenu.tsx: mark trigger text/chevron for desktop collapsed presentation; native popover remains usable.
- apps/web/src/localization.tsx: localized collapse/expand labels.
- apps/web/scripts/collapsible-navigation-browser.mjs: synthetic fixtures, geometry, keyboard, persistence, draft, profile, company and mobile acceptance.
- docs/WEB_SPEC.md: durable navigation contract.

## Research and Alternatives
Reuse the same anchor links in both modes. Separate rail markup would duplicate navigation rules. Keep the global company header intact to preserve the Web invariant; do not hide the company selector. Use localStorage only for one browser preference; no server schema or business state.

## Test Strategy
Browser acceptance for FR-001–004 before implementation: missing toggle fails first. Verify 200→60→200px, 140px content expansion, all link names and titles, keyboard, profile, persistence, chat draft, mobile labels, four languages and blocked storage. Full frontend contracts, formatting, localization audit, TypeScript/Vite build and spec policy. Backend/migration/catalog checks do not apply to this presentation-only change.

## Rollout and Rollback
Normal web bundle. Default expanded for existing browsers. Reverting UI ignores the harmless local preference. No migrations.

## Risks and Review
Check native profile popover, mobile overlay and short viewport scrolling. Desktop-only CSS must not hide mobile labels. Review no duplicate navigation or business writes.

## Complexity Tracking
No exceptions. All Constitution rows pass before and after design.

## Tooltip and toggle refinement

FR-005–006: Replace native titles with a shared SidebarTooltip portal attached to the existing navigation ref. Event delegation serves the existing links, toggle and profile; fixed positioning avoids the scroll container clipping. Dismiss on Escape, blur, pointer departure, scrolling, resize and activation; allow the pointer to enter the tooltip. Use dark background and white text in both themes. Move a plain PanelLeft toggle into the Daily work heading row. No new service or dependency. Constitution Check remains PASS.

Browser proof first: rendered hover/focus tooltip, native title absence, Escape/scroll dismissal and heading/toggle geometry. Repeat existing sidebar acceptance and frontend gates.
