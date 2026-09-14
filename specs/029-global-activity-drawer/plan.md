# Implementation Plan: Global Activity Drawer

Reuse `api.timeline` and `InspectorDrawer` from the React shell. Place the desktop trigger in the reserved sidebar brand row and reuse the existing mobile header below the desktop breakpoint. Do not introduce a page-wide topbar. Add only shell state, a responsive drawer component, Tailwind primitives, and a static contract test. Constitution Check: PASS — no schema, persistence, business-rule, tenant-boundary, or Source → Evidence → Reality change.
