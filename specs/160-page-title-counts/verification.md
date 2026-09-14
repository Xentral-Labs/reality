# Verification

- Pre-change browser proof failed because no main-register title badge existed.
- Browser matrix: 18 main registers plus Actions, Views and Exception catalogs pass.
- Explicit zero, filtered zero, tab changes, failed-read cleanup and recovery pass.
- Nested Technical record overview retains its local count without changing the main badge.
- Navigation removes the previous badge. Mobile 390px title geometry and screenshot inspected.
- Full frontend gate passes: formatting, 76 tests, four-language audit (1221 keys each), TypeScript and Vite production build.
- Spec policy, Ruff and diff whitespace checks pass.
- No backend, API, query or migration changes. Backend execution remains covered by existing main validation and normal PR CI; no repeated local backend suite for this presentation-only change.
- Web image built from the isolated main-based branch and deployed to port 8080 with the existing Finance backend/database retained. The same browser matrix passes against deployed port 8080; proxied health returns 200.

Final review: Count provenance stays with the existing read result. Pagination information, local category counts and bounded nested collections retain their own meaning. No new count request or business mutation is introduced. The shared presenter falls back locally outside the page shell.

## Page-tab refinement

The pre-change browser check failed on the old global-heading layout. Updated
page-chrome proof passes for all ten tab groups at desktop/mobile widths, including
last-tab clicks on narrow strips and three non-English interface languages.
The register-count matrix and populated Finance footer proof still pass.
The complete frontend gate passes (76 tests, four-language audit, formatting,
TypeScript/Vite), as do spec policy, Ruff and whitespace checks. Screenshots
confirm one page heading, tabs below it, no global tab row and no mobile overflow.
No backend/schema/service behavior changed. The deployed proof passes: 44 desktop/mobile layouts and three translations. Port 8080 serves index-DIUwgVIz.js and index-Dt8MiSZ7.css; proxied health returns 200.

## Compact top-row refinement

The large introduction card is absent and every tested destination has one title,
count target and always-visible localized description in the compact 60px header.
The 44-layout desktop/mobile matrix confirms that descriptions stay inside the
header and the document does not overflow horizontally. Title-count and populated
Finance footer regressions pass. The complete frontend gate passes (76 tests,
four-language audit with 1221 keys each, formatting and TypeScript/Vite build), as
do spec policy, Ruff and whitespace checks. No backend, schema, query or business
behavior changed.

The title count uses an 18px responsive superscript badge with a measured gap before
the description. One-, two- and three-digit screenshots confirm a circular-to-capsule
transition with fixed padding; the shared count value, localization and update behavior
are unchanged.
The Commitments main count participates in the same shared geometry; direction-tab
counts remain local to their tabs.
