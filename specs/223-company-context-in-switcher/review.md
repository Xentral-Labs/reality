# Review and verification

## Pre-implementation analysis

Reviewed the specification, plan, tasks and Constitution before the code change. Five
requirements all map to implementation and tests; no ambiguity, duplication, unmapped
requirement or critical finding. The explicit user request authorizes the navigation
change. No schema, stored data, shared business calculation or tool catalog changes.

## Test-first evidence

The navigation assertions in demo-live-browser.mjs (Demo Data present and following
Companies) and retirement-browser.mjs (the Companies navigation link) were rewritten to
the switcher footer and the integrations card before the components changed, so both
described the intended placement while the old one was still in the code.

## Verification

- Frontend contracts: 232 passed.
- Localization audit: English, German, Dutch and Spanish passed, 1895/1895 covered.
- TypeScript project build and Prettier: passed.
- demo-live-browser: passed in four languages, both themes, desktop and mobile,
  including the absent navigation entry, the card content and its absence for an
  ordinary company.
- collapsible-navigation-browser: passed, including collapsed tooltips and mobile.
- unified-sources-browser: passed, 48 localized screenshots.
- Switcher flow: verified with a focused script on the retirement fixtures — no
  Companies navigation link, the footer lists Manage companies and New company, and
  `settings_view=new` opens the creation form and keeps it open across a reload.
- Localized card: German, Dutch and Spanish render the card at 390px with no
  horizontal overflow.

## Known limitation

retirement-browser.mjs is red on main before it reaches this code: it waits for a
sidebar link "Orders & deliveries" that has not existed since spec 160. Its assertions
here were updated but could not be executed; the switcher path was verified with the
focused script described above instead.
