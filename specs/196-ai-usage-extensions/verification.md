# Verification

## Completed checks

- Initial service test collection failed because the new service did not exist.
- Final new service/API regressions: 6 passed. The added membership-removal fixture
  initially used an invalid status; correcting it to `removed` made the test exercise
  actual access revocation. The surrounding final focused run had 20 other passes.
- Focused service/setup/API run: 23 passed before the final additional isolation cases.
- Browser self/admin extension flow passed: preview and cancel cause no grant,
  confirmation does, transient failure retains the same request key, history identifies
  the actor and shows reason/amount, admin +100 works, and four mobile locales fit.
- Existing trial browser passed entry/retry, starter navigation, exhausted draft and
  four localized mobile layouts.
- Web build passed 169 contract tests, four-language audit, TypeScript and Vite.
- Lint, spec coverage policy, generated-catalog consistency and diff checks passed.
- Reviewed mobile Usage screenshot. Historical expiry is labeled Expires, not reset.
- Local API health and authentication boundary verified; no real credits were granted.
  Final local frontend asset: `index-DDAADpXz.js`.

## Completion

Full PostgreSQL suite excluding timing-sensitive integration: 2516 passed, 9 skipped,
one failure from the old membership fixture loaded at worker collection time. The
corrected service/API family passed all 6 tests. The final serial run of the full
PostgreSQL integration file plus that corrected family passed all 16 tests in 34.66s.
No required failing check remains. The original serial run was stopped in favor of
four isolated workers; timing-sensitive integration ran afterward without that load.

Final source review confirms no schema changes, no provider-selection change, no
consumption deletion and no non-admin target control. Grant values remain append-only
security audit entries; calculations read those entries. All planned checks complete.
Local API and web preview updated; no live self extensions consumed. Final UI asset:
`index-DDAADpXz.js`. The implementation is committed locally. Updating PR 15 is pending explicit user
approval: automatic review rejected the push despite verification of the existing
repository/branch, citing lack of explicit approval for this payload transfer.
