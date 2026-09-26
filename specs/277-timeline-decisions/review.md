# Implementation Review: Decision points in the business timeline

## Scope review

The implementation adds only presentation-time markers derived from the existing decision register. It neither writes BusinessEvents nor infers proposal-to-order membership. All-activity shows the lane; selected-order mode omits its tenant-wide points. Decision markers do not participate in held relationship edges.

## Verification

- `node --test --experimental-strip-types scripts/order-journey-layout.test.mjs`: 6 passed.
- `npm run test:contracts`: 399 passed.
- `npm run build`: passed (existing bundle-size warning only).
- `npm run i18n:audit`: all 2,281 keys covered in English, German, Dutch and Spanish.
- `make spec-check`: passed.
- Prettier check and `git diff --check`: passed.
- `order-journey-browser.mjs` now asserts six lanes, four lifecycle points for accepted/rejected fixtures, and zero decision points after order selection. Execution remains for the external Playwright/Vite browser harness.

## Risk review

The two register reads are bounded at 100 pending and 100 settled decisions. A visible partial-history notice appears when either result is truncated. A read failure preserves prior markers and uses the existing history retry state. There is no migration or rollback risk.
