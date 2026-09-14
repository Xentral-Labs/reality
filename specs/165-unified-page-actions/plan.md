# Plan: One page action bar

Add `apps/web/src/unified/PageActionBar.tsx`: a `PageAction` type (key, label, handler,
disabled) and a `PageActionBar` that filters falsy entries, renders every available action
inside the existing `RegisterActions` disclosure, and portals the result through
`PageActions`. Add
`useContextActions(placement, { onOpen, exclude })` beside `ContextActions` in
`ActionLauncher.tsx`; it maps `menuEntries` to `PageAction`s with the existing `launch`
handler and returns an empty list until the discovery read has data.

Remove the `actions` and `pageActions` props from `RegisterToolbar`; pages render
`<PageActionBar actions={…} />` themselves. `WorkHeader` takes `actions` instead of
children. Companies, Integrations (a request counter opens the preparation editor from the
page), Master data (family label), Sales/Purchasing, Warehouse, Finance and Exceptions
declare their lists; Decisions moves its note into the filter row; Profile & preferences
unwraps its Save button. Scope the compact 34px button rule to the register toolbar and the
menu entries so header buttons keep the 40px header height. Update `docs/WEB_SPEC.md` and
the coverage matrix. Implementation touches only web adapters; no domain, service, tool,
API or persistence change.

## Constitution Check

All principles PASS. No schema, authority, mutation, confirmation or business calculation
changes; discovery eligibility, tenant scope and Source → Evidence → Reality links are
untouched. Owner approved the scope; every requirement maps to a task and a scenario.

## Verification and rollback

Extend `apps/web/scripts/unified-app-contract.test.mjs` with a page-action contract that
fails while any page still writes into the slot directly or the toolbar keeps its action
slot. Update the browser scripts that opened the menu unconditionally to open it only when
present, and the action-discovery browser assertions to read the bar. Run the frontend
contract suite, the action-discovery, workspaces, tables, sources, finance, orders,
opening-stock, item-import, source-configuration, settings and integrations browser suites,
plus a desktop boundary assertion. The shell header uses the body's responsive navigation,
content and optional-chat columns; its heading/actions occupy the middle column. Run the
TypeScript/Vite build, four-language localization audit, Prettier and spec gate.
Rollback reverts this UI commit; no migration or data operation.

Render the existing CompanySwitcher in two responsive shell locations: desktop navigation
before Daily work and mobile header controls. CSS makes exactly one location available at
each breakpoint; the shared component, company state and switch handler remain unchanged.
Render HeaderControls as the header's independent third child so desktop global utilities
remain right-aligned above chat; mobile retains the existing combined controls disclosure.
Move PageActionBar's portal target from the global header into a shared local row containing
the existing RegisterHeader tabs target on the left and actions on the right. Keep the row
when either side has content. Exceptions removes its PageActionBar declaration and renders
the catalog opener in its existing filter row; Companies uses the action-only local row.
