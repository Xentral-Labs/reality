# Implementation Plan

## Technical Context

React/TypeScript frontend only. No backend, schema, service or dependency changes.
The switcher, the settings page and the integrations page already exist; this moves
existing destinations between them and adds one presentational card.

## Constitution Check

| Principle | Result |
|---|---|
| Source → Evidence → Reality | PASS: no record changes |
| Reality authority | PASS: presentation of existing reads only |
| Proven schema | PASS: no schema changes |
| Tenant/service boundaries | PASS: existing tenant-scoped reads, no new endpoint |
| Spec and test evidence | PASS: explicit user request, browser assertions updated first |
| Explainable Web | PASS: the simulation is named where its records enter |
| Simplicity/storage | PASS: one duplicate list and one navigation entry removed |
| Received values | PASS: state, rate and last import are displayed as received |

## Design and implementation order

Update the browser assertions that pin the removed navigation entries first
(demo-live-browser.mjs, retirement-browser.mjs), so they fail before the change.

Add `new` to the settings section union and its allow-list in routing.ts. Lift the
creation form's local state into the address: SettingsPage.tsx passes `creating` and
`setCreating` to CompanySettings.tsx, which loses its `useState`.

Give CompanySwitcher.tsx the selection and navigate props, a per-row simulation state
line and a footer with Manage companies and New company; style the state line in
tailwind.css beside the existing sandbox badge.

Remove the Companies and Demo Data entries from Shell.tsx and pass the new switcher
props there.

Add DemoDataSource.tsx: an eligibility predicate over the bootstrap tenant plus a card
that reads the demo-data status, listens for `reality:demo-data-changed` and links to
the simulation route. Render it at the top of the systems view in DataSourcesPage.tsx,
which receives the company from UnifiedApp.tsx.

Add the six new strings to the German, Dutch and Spanish dictionaries and align
"Manage companies" with the app's own Unternehmen wording. Update docs/WEB_SPEC.md.

## Verification

Frontend contracts, the four-language localization audit, `tsc -b`, Prettier, and the
demo-live, collapsible-navigation and unified-sources browser suites. Verify the
switcher footer and the address-driven creation form with a focused script, because
retirement-browser.mjs is red on main before reaching this code. Capture the card in
all four languages at 390px and 1440px. Record failures without marking tasks complete.
Rollback restores both navigation entries and the local creation state.

## Complexity Tracking

None. No backend, domain, persistence or tool registry work.
