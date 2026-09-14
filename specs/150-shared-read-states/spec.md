# Feature Specification: Shared read states in the unified app

**Created**: 2026-09-09
**Status**: Implemented; local web gates verified
**Language**: English

## Context and Intent
### Problem
Every read in the unified app announced itself as the sentence "Loading…" inside a
bordered card. Inside a register that card sat within the register surface's own
border, so a page that was about to show a full table first showed an empty
border-inside-a-border box roughly seventy pixels tall. Worse, `useRead` discarded the
answer already on screen on every reload, so changing a filter chip, paging, sorting,
or a settled delivery collapsed a full table to that box and then jumped back. Facts
and Inspector records collapsed even when an answer was already held, because their
gate tested `loading` rather than the absence of data.
### Scope
One shared read-state language for the unified app: a placeholder shaped like the
answer for a first read, previous content dimmed in place for a reload, and the
existing card with retry for a failure.
### Non-Goals
No new progress indicators, spinners, percentage estimates, optimistic or cached
answers across sessions, prefetching, service worker, request deduplication, change
to any read contract or API, and no new business behavior or persistence.
### Existing Contracts
[Web](../../docs/WEB_SPEC.md) shared-state rule; the register workbench of spec 137
and the unified app of spec 139 keep their layout, filters, paging and inspection.

## User Scenarios & Testing
### US1 — Change a filter without losing the table (P1)
A user narrowing deliveries by direction or scope, paging, sorting or resizing keeps
the rows already on screen. Those rows dim and report themselves busy while the next
answer loads, then are replaced in place.
Acceptance: a filter change never removes the table from the page; the register keeps
its height; the toolbar and the control just used stay at full contrast and stay
operable; a screen reader reports the region busy. Switching company or register view
still shows a placeholder, because the previous answer no longer describes the request.
### US2 — Do not be told that something is loading (P1)
A first read shows bars in the shape of the answer that is coming, with no border of
its own, and only once the read is slow enough to notice. A read that returns quickly
shows no placeholder at all.
Acceptance: the placeholder carries no border inside the register surface; it is
revealed only after 200 ms; it exposes an accessible loading status without prose; it
is the same component on every page and inside cards.
### US3 — See a failure, not a silent gap (P1)
A failed read keeps the existing card with the reason and a retry action.
Acceptance: a reload that fails discards the previous answer rather than leaving a
stale table standing in for a read that did not happen; the error and retry are
reachable; retry repeats the same read.

## Requirements
- **FR-001**: `useRead` keeps the previous answer while the next read of any query is in
  flight and replaces it on success. A failed read discards it and reports the reason.
  Company changes still unmount consumers; obsolete responses are still discarded.
- **FR-002**: One shared component renders every read placeholder. Loading draws a
  bounded number of bars sized like the answer, carries no border, exposes
  `role="status"` with an accessible name, and states nothing in prose. Failure keeps
  the existing bordered card with reason and retry.
- **FR-003**: The placeholder is revealed only after 200 ms, in CSS, so a fast read
  never flashes one. Reduced-motion preference removes the pulse and keeps the delay.
- **FR-004**: Register results dim in place while a newer read is in flight, through the
  shared register table rather than per-page markup, and mark the scrolled region
  `aria-busy`. Toolbars, filters and actions stay at full contrast and remain operable.
- **FR-005**: A page shows a placeholder only when it holds no answer for the current
  request. A view or company change still counts as no answer, through the discriminator
  guards the register pages already apply.
- **FR-006**: Single-value reads inside cards, dialogs and pickers use the same shared
  inline placeholder instead of the word "Loading…". Busy button labels and select
  placeholders keep their text.
- **FR-007**: Four languages, both themes, mobile and keyboard behavior are unchanged;
  no new user-facing string is introduced.
- **DR-001**: No read contract, projection, schema or business rule changes. Placeholders
  and busy marks are presentation only and never stand in for a recorded value, so
  Source → Evidence → Reality and tenant scope are untouched.

## Success Criteria
- **SC-001**: No register page removes its table from the DOM for a filter, page, sort or
  settled-delivery reload of the same view.
- **SC-002**: No unified page states loading in prose; the shared components are the only
  loading presentation.
- **SC-003**: A failed reload always surfaces reason and retry, never a stale table.
- **SC-004**: `npm run test:i18n`, `npm run i18n:audit`, `npm run format:check` and
  `tsc -b` stay green; the new contract assertions fail against the previous source.

## Assumptions and Dependencies
`UnifiedApp` keys route content by user and company, so keeping data across reloads
cannot show another company's answer. Orders, Warehouse, Finance and Data sources
already compare the held answer's view against the selected view, so a view switch
still shows a placeholder. 200 ms is chosen as the threshold below which a placeholder
costs more than it explains; it is a CSS animation delay, not new state. Reads that
resolve to `null` by design, such as Inspector records under the Facts kind, keep
rendering nothing rather than a placeholder.

## Open Questions
None. Reported by the owner from the live local stack with screenshots of the delivery
and stock registers.

## Requirement Traceability
FR-001/005 → `apps/web/src/unified/useCompanyContext.ts`, the register page gates, and
the "a reload keeps the answer already on screen" contract test.
FR-002/003/006/007 → `apps/web/src/unified/ReadState.tsx`, `apps/web/src/tailwind.css`,
the card and picker call sites, and the "one shared read placeholder" contract test.
FR-004 → `apps/web/src/unified/RegisterTable.tsx` and the `busy` assertions.
DR-001 → no change under `packages/reality-core/`.
SC-001–004 → `apps/web/scripts/unified-app-contract.test.mjs` plus the web gates.
