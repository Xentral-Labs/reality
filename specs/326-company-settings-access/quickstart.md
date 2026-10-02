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

Full targeted backend rerun: **149 passed** in 228.20 seconds, two PostgreSQL workers. Full frontend verification: **458 contract tests passed**, formatting and all four language audits passed, TypeScript and Vite production build passed. Hosted CI and deployment completed; public release verification passed. The existing-session native UI post-deployment check remains blocked as recorded below.

Before deployment, public MCP discovery advertises its own MCP origin as authorization server. After this fix it must advertise the configured API origin. The authenticated owner settings read returns Internal Server Error before deployment. No live credentials, grants or business data were altered.

## Final Code Review
The configuration correction preserves all public-origin and production HTTPS checks. Runtime-only values do not affect endpoint display. The report membership lookup is unchanged; only list-context wording differs, while detail and mutation paths retain generic NotFound. Company owner actions retain their original condition. No schema, stored permission, credential or business record changed. Generated catalogs have no diff. All local planned gates and all 22 hosted PR checks are green. Publication/deployment completed; the native existing-session UI post-check remains explicitly open.

## Hosted Release Evidence — 2026-10-02

- [PR #292](https://github.com/Xentral-Labs/reality/pull/292): **22/22 checks succeeded**, including the complete four-shard PostgreSQL suite, frontend quality, seven fixture browser shards, live browser journeys and documentation quality. [Quality run](https://github.com/Xentral-Labs/reality/actions/runs/37028734858).
- Rebase merged under the owner's explicit session authorization. Main commit: `1fd4363e009e746e104b91c1bbf1f4c425dcb6ba`.
- [Deploy run](https://github.com/Xentral-Labs/reality/actions/runs/37030190445): all six role images and GitOps notification succeeded. [GitOps receiver](https://github.com/Xentral-Labs/argocd/actions/runs/37030407744): succeeded; desired image tag `1fd4363`.
- Public API `/healthz` returned healthy and MCP `/readyz` returned ready. Served Web entry `index-BQRGeO3y.js` contains the new no-membership label; workspace bundle `UnifiedApp-BRLZBVhn.js` is the deployed release.
- Public MCP discovery now advertises `https://app.runreality.ai` as authorization server for `https://mcp.runreality.ai/`; before rollout it advertised its own MCP origin. Discovery has a one-hour public cache header, so callers may need a fresh read after rollout.
- No live credentials, grants, private reports or business records were changed during verification.

### Remaining Existing-Session UI Post-Check

Before the fix, the authenticated owner endpoint was observed returning Internal Server Error. After rollout, native Computer Use returns `-10005: cgWindowNotFound` for Chrome. Fresh app selection by name and bundle ID, surface inventory, and a reset/reconnection reproduced the failure; Chrome is listed running, but no usable window is available. No alternative technique accessed its session or credentials. The user was asked asynchronously to make Chrome visible after returning. The actual post-deployment owner dialog result is therefore **not claimed as observed**. The authenticated owner/member API regression and all four-language settings/report browser proofs are green; T013 remains open until the native window can be read.

## Existing-session completion (2026-10-02)

After Chrome became visible, native Computer Use verified the deployed company page: test showed Owner; the two companies without membership showed No company membership. Agents & API tokens loaded its connected-client/manual-token sections and empty active-token list without error. AI configuration displayed AI credentials configured and Managed by Reality. The nonmember private report library explained that an active company membership is required. No credentials, grants, membership or business records were changed. T013 is now complete.

## Access-state browser proof (2026-10-02)

The new membership-heading assertion failed before the UI change. After the change, `analytics-save-clarity-browser.mjs` passes all four languages: access heading and owner/switch-company guidance, no technical loading-error title, Check access again, current-response recovery, no writes and normal saved-report journeys. Prettier, TypeScript/Vite production build, four-language i18n audit (2553/2553 covered each), spec policy and generated catalog parity pass. Hosted CI remains required before completion.

## Published gateway and access-state completion (2026-10-02)

PR [296](https://github.com/Xentral-Labs/reality/pull/296) passed all 22 hosted gates at head `128eeb367f7f18be3befa1fdec72a464e5d078ee`; quality run [37035559686](https://github.com/Xentral-Labs/reality/actions/runs/37035559686) completed successfully on attempt 2. The only repeated group was browser shard 6: its initial Playwright installation stalled before tests, so the remaining job was canceled and rerun individually; all 21 other successful gates were retained. No product change was needed for the retry. Rebase merge produced main `cecd1b1d96204347d06b2f671f10b5c08e22425c`. Deploy [37037994680](https://github.com/Xentral-Labs/reality/actions/runs/37037994680) built all six role images and notified GitOps successfully; GitOps [37038188373](https://github.com/Xentral-Labs/argocd/actions/runs/37038188373) selected image `cecd1b1`.

Public post-rollout checks: both authorization discovery documents return HTTP 200 JSON with issuer `https://app.runreality.ai` and canonical authorization/token/revocation endpoints. Missing protocol parameters at `/oauth/authorize` return HTTP 422 JSON from API validation; interaction-only authorization URLs still return HTTP 200 SPA HTML. App `/healthz` and MCP `/readyz` return HTTP 200 JSON. No live grant or token was created.

Native Computer Use in the existing authenticated Chrome session observed the new nonmember report heading, owner/switch-company guidance, and Check access again; pressing that read-only control retained the current access explanation without a technical loading error. The active owner company loaded its normal empty private-report library. Both owner settings dialogs had already loaded successfully after the settings release. Existing membership and private-report authorship were not changed. All regression-repair tasks are complete.
