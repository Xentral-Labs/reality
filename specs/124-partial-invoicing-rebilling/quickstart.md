# Validation
In isolated data, invoice 2 of 5 units, then the remaining 3; reject an excess unit. Reverse the 2-unit invoice and rebill 2 with independently stated money. Verify payment reversal does not release units, unposted evidence consumes units and multi-group invoices require all groups reversed. Repeat for supplier and multi-position invoices. Check stale/concurrent work and unchanged historical receipts. Run full required core/web/browser gates; shared preview checks read only.

## Verification
- Failing proof: eight new tests failed against the previous implementation (`/private/tmp/reality-124-red.log`).
- Focused invoice/reversal regression: 52 passed; added HTTP/tenant proof: 10 partial-invoice tests passed (`reality-124-focused.log`, `reality-124-extra.log`).
- Shared preview login and form read: same user and five tenants on 5177/8080; add/remove selection and availability passed without preparing or confirming business actions (`reality-124-shared.log`).
- Complete backend: **1,633 passed, 7 existing skips** (`/private/tmp/reality-124-backend-final.log`).
- Frontend: build, 131 contract tests, i18n tests, all 1,645 translation keys in four languages and format check passed (`reality-124-build.log`, `reality-124-contracts.log`, `reality-124-i18n-tests.log`, `reality-124-i18n.log`, `reality-124-format-check.log`).
- Invoice/reversal/payment/Finance intercepted Chrome journeys passed, including responsive and localized layouts. Screenshots are under `/private/tmp/reality-124-invoice-browser` and `/private/tmp/reality-124-reversal-browser`; German desktop/mobile and actual shared form were visually reviewed.
- Ruff, spec policy and `git diff --check` passed. No migrations or schema changes.

## Final review
FR-001–006 complete. Matching invoice evidence and complete original-group reversal state define availability; unposted/excess source evidence remains intact. Shared tenant locking serializes direct/proposed invoice writers and related evidence/posting/reversal mutations. Review snapshots are separate from immutable creation receipts, so old verified invoices and reversals remain verifiable after rebilling. UI never calculates business availability independently. Pending reviews made before this increment may need refreshing. No shared financial test mutations, deployment, merge or legacy retirement occurred.
