# Validation
Using isolated PostgreSQL: post customer/supplier invoices and partial payments; preview/reverse each group and compare projected and actual open/unallocated amounts. Change a counterpart after review and verify stale rejection. Recover a lost response using event proof, then make a later financial change and retain historical verification. Test missing/foreign/reversing groups and malformed evidence. Run full core and frontend/browser gates. Shared preview uses only login, selection and reason editing; no financial test confirmation.


## Verified result — 2026-09-08
- Complete isolated core suite: 1,623 passed, 7 existing skips.
- Focused reversal proofs: 15 passed, including both financial directions, exact effects,
  active/inactive allocations, actor/practice policy, scoped HTTP choices/confirmation,
  concurrent payment/reversal, rollback, attribution tampering and historical recovery.
- Frontend: 131 contracts passed; build/formatting and all 1,637 translation keys in four
  languages passed. Reversal browser covers four entry points, edit/reject, reload,
  lost-response recovery and 16 responsive light/dark views.
- Existing invoice, payment and finance browser regressions passed.
- Shared preview: same users/session and five tenants as port 8080. Current selected company
  has zero reversible groups; authenticated choice/empty-state and reason editing passed.
  No test proposal or financial reversal was prepared/confirmed in the shared database.
- Ruff, specification policy and git diff whitespace checks passed.

Logs: `/private/tmp/reality-123-backend-final.log`, `reality-123-focused-final.log`,
`reality-123-contracts.log`, `reality-123-build.log`, `reality-123-i18n.log`,
`reality-123-format.log`, `reality-123-browser-final.log`,
`reality-123-invoice-entry-regression.log`, `reality-123-payment-entry-regression.log`,
`reality-123-finance-regression.log` and `reality-123-shared-check.log`.
Screenshots: `/private/tmp/reality-123-browser/` and `reality-123-shared-form.png`.

## Final review
All FR-001–006 map to completed tasks and executable evidence. Original failures demonstrated
missing common reversal eligibility. Subsequent review confirmed exact canonical inverse,
current-state effects, bidirectional unresolved overlap, attribution and recoverable receipts.
The practice fixture uses a new practice tenant because tenant purpose is immutable. Browser
Actions tests select the visible menu control; the shared check supports its actual empty data.
No financial rules moved into the browser, no new schema/event vocabulary, and no bank execution,
credit/refund/rebilling behavior, deployment or legacy retirement is included.
