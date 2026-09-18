# Verification

- `gmake web-build spec-check`: PASS, including 237 frontend tests, all four language audits (1,905 keys), TypeScript and production Vite build. Existing bundle-size advisory remains.
- Prettier on all changed frontend files and `git diff --check`: PASS.
- Existing refined-shell browser flow: PASS, including native menus, appearance, drafts and 32 localized layouts. An initial run timed out locating the account trigger; repeating with selector diagnostics completed the entire flow successfully.
- Existing collapsible-navigation browser: PASS, including keyboard account access, persistence, mobile and localization.
- Explicit temporary preview inspection: PASS for email-only accounts with a long email at desktop/mobile widths in English, German, Dutch and Spanish. Full email text and absence of horizontal menu overflow were checked. German desktop/mobile screenshots were visually inspected.
- The historical retirement browser script cannot reach its account checks: its pre-existing fixture lacks `/api/company-setup/playground` and still expects the old Orders & deliveries navigation. Its account label selectors were updated, but no pass is claimed for that script. The focused shell and account checks above cover this presentation change.

No backend, API, database or executable catalog changes; their suites and documentation regeneration are not applicable. CI will run the repository's required PR gates. Main was verified as `84b3e8ef` before preparing this PR. The original dirty checkout was left untouched.
