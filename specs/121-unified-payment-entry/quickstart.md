# Validation
Run isolated `pytest -q tests/test_unified_payment_entry.py tests/test_finance_payment_atomicity.py`
from the core package, then the full suite. Run web contracts/build/i18n/format and payment/browser
regressions. In a disposable test company, record part of an invoice's open amount, inspect the
remaining amount, then settle the remainder. Reject stale review and recover a lost response.
Verify historical receipt after payment reversal. Shared preview smoke is login/form reads only.


## Verified result — 2026-09-08
- Full isolated core suite: 1,593 passed, 7 existing skips.
- Focused payment/atomicity suite: 39 passed, including precision rejection and exact
  representable amounts, both directions, partial settlement, reversal and concurrency.
- Frontend: 131 contracts passed; build and formatting passed; all 1,617 translation keys
  covered in English, German, Dutch and Spanish.
- Payment browser: Finance/Actions/Chat/Decisions, partial amount review, edit/reject,
  reload, lost-response recovery, exact decimal display and 16 localized responsive views.
- Existing invoice-entry, order-entry and finance browser regression journeys passed.
- Ruff, specification policy and git diff whitespace checks passed.
- Shared preview: same login/session/user and five tenants as port 8080; payment form reads
  passed. No test business mutation was prepared or confirmed in the shared database.

Evidence logs are under `/private/tmp/reality-121-`: `backend-final.log`,
`precision-green.log`, `contracts.log`, `build.log`, `i18n.log`, `format.log`,
`browser.log`, `invoice-entry-regression.log`, `order-entry-regression.log`,
`finance-regression.log`, `shared-check.log`, `lint.log` and `spec.log`.
Screenshots: `/private/tmp/reality-121-browser/` and `reality-121-shared-form.png`.

## Final review
FR-001–007 map to completed T001–T006 and the executable proofs above. Review confirmed
shared tenant-scoped services, explicit current-state confirmation, canonical ledger-only
receipts, original-source availability, no silent payment rounding and separate historical
proof/current observations. The first full run was intentionally interrupted when precision
review found a gap; the focused regression was observed failing before the guard was added,
then the complete suite was rerun against frozen core sources. No schema, new event vocabulary,
bank execution, deployment, legacy retirement or constitutional exception was introduced.
