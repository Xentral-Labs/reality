# Verification Guide
Use the existing isolated PostgreSQL test fixture in UTC. Run configuration and settings API tests, private-report lifecycle/surface tests, and owner authorization tests with PYTHONPATH=src. Run make lint, make spec-check, make web-build, settings/analytics browser scenarios, make docs-generate and make docs-catalog-check. Hosted CI is the complete required suite. After green review/merge, verify deployment image revision and both logged-in settings dialogs; inspect missing-membership company and report views without mutating credentials or business records.

## Evidence
Meaningful failing proofs observed before correction: production settings endpoint and MCP runtime configuration; membership-required service cases; browser missing-membership card. The removed-membership fixture uses the actual `removed` status, and HTTP proof overrides both existing API/auth database dependencies.

Green local evidence so far:
- Ten focused configuration/settings/membership regressions.
- Corrected platform-administrator private-library HTTP proof.
- Authenticated settings API member denial and owner success.
- Settings browser: absent/owner/member roles, owner isolation and retry, secret exclusion, 48 localized screenshots.
- Analytics browser: membership refusal and retry in en/de/nl/es plus existing save journeys.
- Ruff, spec policy, generated documentation parity and diff whitespace.

Full targeted backend rerun: **149 passed** in 228.20 seconds, two PostgreSQL workers. Full frontend verification: **458 contract tests passed**, formatting and all four language audits passed, TypeScript and Vite production build passed. Hosted CI, deployment and live verification remain release gates; their final evidence is recorded in the pull request and a completion documentation update.

Before deployment, public MCP discovery advertises its own MCP origin as authorization server. After this fix it must advertise the configured API origin. The authenticated owner settings read returns Internal Server Error before deployment. No live credentials, grants or business data were altered.

## Final Code Review
The configuration correction preserves all public-origin and production HTTPS checks. Runtime-only values do not affect endpoint display. The report membership lookup is unchanged; only list-context wording differs, while detail and mutation paths retain generic NotFound. Company owner actions retain their original condition. No schema, stored permission, credential or business record changed. Generated catalogs have no diff. All local planned gates are green; publication/deployment completion remains pending.
