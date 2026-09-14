# Validation
In isolated tests, create a two-position order and record a two-position invoice in both directions. Supply a header total different from line sum and verify every value remains unchanged. Check invalid second position leaves no invoice/source/postings; stale and overlapping actions cannot repeat billing. Recover a lost response and verify every line link. Run all core tests and frontend/browser gates. Shared local preview login/form inspection only; no financial test mutations.


## Verified result — 2026-09-08
- Full isolated backend suite: 1,608 passed, 7 existing skips.
- Multi-position proofs: 15 passed; earlier invoice/payment/practice focused regression: 122 passed.
- Frontend: 131 contracts passed; build, formatting and four-language audit passed (1,620 keys).
- Invoice browser: add/remove positions, two-position edit preservation, independent stated total,
  both directions, all four entry points, reload and lost-response recovery; 16 localized
  responsive light/dark reviews. Existing payment and finance browser regressions passed.
- Existing shared login/session and five tenants remain available; new form selection/add/remove
  passed against the running preview. No financial test proposal or invoice was created there.
- Ruff, specification policy and git diff whitespace checks passed.

Logs: `/private/tmp/reality-122-backend-final.log`, `reality-122-focused-final.log`,
`reality-122-focused2.log`, `reality-122-contracts.log`, `reality-122-build.log`,
`reality-122-format.log`, `reality-122-i18n.log`, `reality-122-browser-final.log`,
`reality-122-payment-regression.log`, `reality-122-finance-regression.log` and
`reality-122-shared-check.log`. Screenshots: `/private/tmp/reality-122-browser/`
and `/private/tmp/reality-122-shared-form.png`.

## Final review
All six requirements map to completed tasks and executable proofs. Initial tests were observed
failing on unsupported multi-position input; shared core validation and atomic recording then
passed both directions, stale/overlapping work, rollback and exact receipt recovery. Existing
single-position tests remain unchanged. Browser edit assertions wait for the asynchronous form
response. No new schema, event/tool name, alternative adapter business rule or constitutional
exception is introduced. Scope remains same-order positions; repeated partial billing, financial
corrections and rollout/retirement are separate.
