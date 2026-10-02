# Validation

Use an isolated PostgreSQL test cluster through TEST_POSTGRES_ADMIN_URL. Run the complete reporting lifecycle/surfaces, requested-analysis and proposal-policy modules with pytest. Run unified-settings-browser.mjs with synthetic identity fixtures in all four languages and analytics-save-clarity-browser.mjs for ordinary nonmember/access recovery. Run make lint, make spec-check, make docs-catalog-check and the web format/contracts/build/i18n gates. Require all hosted PR checks green. After deployment, use native Chrome in the existing authenticated admin session to read My reports in a company without membership and inspect truthful switcher/card labels. No production role assignment, token issuance or private report creation is needed.

Verification evidence is recorded below.

## Local Verification (2026-10-02)

New eligibility tests failed before implementation: persisted admins without membership were denied report creation, HTTP library access and deferred admission/worker journeys. The UI admin-label assertion failed before presentation implementation. After implementation, all 102 tests in reporting lifecycle/surfaces, requested analysis and proposal-policy modules passed; three additional planned admin cross-company/private-request/sealed-own-proposal tests passed separately (105 total). Ordinary membership refusal, foreign private author/report mutations, forged/stale principal, inactive/revoked account, unavailable/practice tenant and worker revalidation remain covered. No membership is created.

The settings browser script passes original owner/member/nonmember rules, profile recovery, 48 localized screenshots, and new four-language admin/card/switcher assertions. The analytics-save-clarity browser script passes ordinary nonmember refusal/recovery and saved-report journeys. TypeScript/Vite build, Prettier, four-language i18n audit (2555/2555 each), core Ruff, spec policy, generated docs parity and whitespace checks pass.

## Hosted and Live Verification (2026-10-02)

[PR #301](https://github.com/Xentral-Labs/reality/pull/301) passed all 22 checks in [quality run 37044689338](https://github.com/Xentral-Labs/reality/actions/runs/37044689338), including the complete PostgreSQL suite, frontend contracts, seven browser-script groups and six live-browser journeys. The reviewed head was d813f3649a87091a049cb12f8e629ebdf1f4f950; its merge is 10cd775dbfbf376c7b0beb5716748596e4df50a9.

[Deploy run 37045841899](https://github.com/Xentral-Labs/reality/actions/runs/37045841899) built and published all six deployment roles successfully. [GitOps run 37046067454](https://github.com/Xentral-Labs/argocd/actions/runs/37046067454) succeeded and selected image tag 10cd775.

Read-only native Chrome checks in the existing authenticated platform-admin session confirmed that My reports opens normally in both Bene AG and PleaseIgnore, where this account has no membership. Each library showed its normal empty state rather than a membership refusal. The switcher and company cards show Platform admin access for both companies and preserve Owner for test. Both admin cards explain that private reports remain personal to their author and expose no owner-management buttons. No membership, token or private report was created. The owner AI configuration dialog also opened correctly after a fresh load. One initial request timed out during deployment; the public entry point subsequently returned HTTP 200 and the repeated authenticated checks succeeded.

Foreign-author, cross-company, forged/revoked/inactive authority and deferred-worker privacy checks use isolated test fixtures, not production private reports. The user explicitly authorized self-review and release; the requirement/privacy checklists and final diff were reviewed accordingly. No schema or public tool contract changed.
