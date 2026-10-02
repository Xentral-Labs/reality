# Validation

Use an isolated PostgreSQL test cluster through TEST_POSTGRES_ADMIN_URL. Run the complete reporting lifecycle/surfaces, requested-analysis and proposal-policy modules with pytest. Run unified-settings-browser.mjs with synthetic identity fixtures in all four languages and analytics-save-clarity-browser.mjs for ordinary nonmember/access recovery. Run make lint, make spec-check, make docs-catalog-check and the web format/contracts/build/i18n gates. Require all hosted PR checks green. After deployment, use native Chrome in the existing authenticated admin session to read My reports in a company without membership and inspect truthful switcher/card labels. No production role assignment, token issuance or private report creation is needed.

Verification evidence will be appended after checks pass.

## Local Verification (2026-10-02)

New eligibility tests failed before implementation: persisted admins without membership were denied report creation, HTTP library access and deferred admission/worker journeys. The UI admin-label assertion failed before presentation implementation. After implementation, all 102 tests in reporting lifecycle/surfaces, requested analysis and proposal-policy modules passed; three additional planned admin cross-company/private-request/sealed-own-proposal tests passed separately (105 total). Ordinary membership refusal, foreign private author/report mutations, forged/stale principal, inactive/revoked account, unavailable/practice tenant and worker revalidation remain covered. No membership is created.

The settings browser script passes original owner/member/nonmember rules, profile recovery, 48 localized screenshots, and new four-language admin/card/switcher assertions. The analytics-save-clarity browser script passes ordinary nonmember refusal/recovery and saved-report journeys. TypeScript/Vite build, Prettier, four-language i18n audit (2555/2555 each), core Ruff, spec policy, generated docs parity and whitespace checks pass. Full hosted CI and deployed native Chrome checks remain required before release completion.
