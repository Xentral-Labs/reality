# Validation Quickstart: OAuth MCP User Access

This guide defines the runnable acceptance evidence to collect after implementation.
It is not an implementation script and does not authorize live deployment.

## Recorded implementation gates

- 2026-09-24: cross-artifact analysis found the planned OAuth HTTP test family is not
  implemented yet; `make spec-check` remains red until that test-first work exists.
- 2026-09-24: MCP Python SDK 2.2.0 was pinned (`mcp>=2.2,<3`), its executable probe
  reported `LATEST_PROTOCOL_VERSION == "2026-07-28"`, and the dedicated stateless
  HTTP runtime completed an authenticated initialize request while retaining a
  separately configured public resource URL.
- 2026-09-24: foundational service and HTTP OAuth proofs passed, covering interaction
  expiry, PKCE code replay, hashed credentials, refresh rotation/reuse, revocation,
  RFC 8414/OIDC metadata, RFC 9207 `iss`, exact redirect/resource checks, current-tool
  preselection with an exact frozen approved subset, and ready Sandbox eligibility.
  Migration 0093 also passed empty up/down/up plus populated downgrade refusal (`3
  passed`).
- 2026-09-24: focused Spec 265 gate passed: `make spec-check`, Ruff across all touched
  backend/MCP/migration files, and the combined OAuth/MCP/migration/Sandbox selection
  (`36 passed, 1 skipped, 502 deselected`). The skip is the archived-Sandbox branch of
  the positive ready-Sandbox credential test; archived/unready refusal remains covered.
- 2026-09-24: immutable principal and server-owned actor propagation checks passed
  (`4 passed, 26 deselected`), including tenant mismatch refusal, context cleanup and
  absence of tenant/user authority fields from public MCP tool schemas; Ruff remained
  green for the touched MCP dispatcher and contract tests.
- 2026-09-24: the complete MCP adapter contract passed after aligning its assertions
  with MCP SDK 2 `CallToolResult.content` and closed union-schema branches (`28 passed,
  2 skipped`); the skips are retired server-rendered UI coverage owned by the React/API
  boundary.
- 2026-09-24: the complete OAuth HTTP contract passed (`13 passed`), including public
  endpoint coverage for exact pre-registration/CIMD acceptance and rejection of
  insecure URLs, private targets, redirects, oversized metadata, timeouts and DNS
  rebinding without creating an authorization interaction.
- 2026-09-24: the complete OAuth service contract passed (`14 passed`), including live
  denial after account disablement, membership removal and company archival; wrong
  company/client/resource refusal; and frozen exact-tool intersection with current
  scopes and catalog growth. Composite manual/interactive verification remains on the
  shared token-verifier path.
- 2026-09-24: the complete MCP adapter contract passed after principal-only MCP
  dispatch and verified human confirmation attribution (`30 passed, 2 skipped`). The
  business story proves proposal creation has zero immediate business effect, explicit
  confirmation performs the mutation, and the resulting decision records the
  authenticated user without exposing actor or tenant fields as client input.
- 2026-09-24: the complete US2 authority/proposal/tenant slice passed (`58 passed, 2
  skipped`). Manual and interactive principals returned the same retained order trace
  from SourceRecord through Document/DocumentLine to Commitment (apart from the live
  observation timestamp), while the same opaque order ID under a foreign principal was
  not found. The skips remain the retired server-rendered UI tests.
- 2026-09-24: the US1 Web implementation passed TypeScript/Vite production build,
  Prettier, the four-language audit (`2192/2192` in en/de/nl/es), and all nine entry
  routing tests. Login return accepts only one bounded opaque interaction ID; browser
  code receives only a fixed same-origin completion path while the short-lived code is
  carried in an HttpOnly cookie. The OAuth HTTP suite passed (`14 passed`) including
  completion-cookie clearing and final server-owned client redirect.
- 2026-09-24: the independent US1 Chromium journey passed against an isolated current
  Vite build using `apps/web/scripts/mcp-oauth-browser.mjs`. It rendered the fixed
  consent route at a narrow viewport, started with all eligible tools selected,
  deselected one tool, distinguished two same-name companies by opaque ID, submitted
  the exact frozen subset, completed cancellation separately, and found no code,
  refresh-token or PKCE marker in URL, DOM, local storage or session storage.
- 2026-09-24: the US3 canonical-setup slice passed its API contract and current
  Chromium journey. Consent and setup-option reads created nothing; company creation
  required its own confirmation and replayed the same request to the same tenant after
  a simulated lost response. The consent UI reused the shared setup form and progress
  flow, returned to the same opaque interaction, selected the exact newly ready tenant,
  and completed for both an ordinary company and an empty Sandbox. Cancelling the
  setup dialog submitted no creation request.
- 2026-09-24: the complete US3 Chromium matrix passed against the isolated Vite build.
  An existing `initializing` request resumed through canonical receipt reads without a
  duplicate create; an `initialization_failed` request required and used the canonical
  retry endpoint before becoming selectable. Completed recovery state was cleared
  before client navigation. A server-declared setup-ineligible account exposed no
  create action and could not approve a grant. The focused PostgreSQL eligibility
  sign-off passed (`7 passed, 1 skipped`): unready/disallowed Sandbox credentials were
  rejected, while a ready practice Sandbox could issue and use manual MCP access under
  the same authority boundary. US3 is complete.
- 2026-09-24: the complete US4 service/HTTP suite passed (`31 passed`) and the combined
  Chromium journey passed against the isolated current Vite build. Personal and
  company-owner inventories showed attributable client, company, exact-tool and
  effective-state metadata in sections separate from manual API tokens. Revocation
  required a distinct confirmation, denied the credential immediately, remained
  isolated from the other grant and was idempotent. A deliberately lost successful
  revoke response produced an unknown state; reload reconciled it as revoked without a
  duplicate mutation. No access token, refresh token or token prefix appeared in the
  DOM, local storage or session storage. The four-language audit passed (`2205/2205`
  for en/de/nl/es). US4 is complete.
- 2026-09-24: the US5 compatibility/failure slice passed its focused PostgreSQL
  regressions (`5 passed`). Existing manual credentials retained their opaque token,
  tenant and exact/wildcard tool behavior while manual and interactive principals used
  the same dispatcher with distinct attribution. An unreachable authorization issuer
  did not interrupt an existing manual credential; invalid and revoked credentials
  remained HTTP 401 with no anonymous fallback. Disabled authorization, unsupported
  clients, issuer changes and changed CIMD redirects failed visibly and were re-read
  without stale acceptance. Manual API responses now identify
  `credential_kind=manual`; telemetry records only bounded credential-kind/outcome
  labels and no credential, user, client or tenant identifiers. The two-client full
  interoperability sequence remains T051.

## Prerequisites

- Python 3.12+ environment with repository dependencies installed.
- Disposable PostgreSQL test database using the repository's normal test fixtures.
- API, Product Web and MCP origins configured separately; production-like validation
  uses HTTPS hostnames.
- Two test human accounts, two ready ordinary companies with overlapping display names,
  one ready Sandbox, one removable membership, and ordinary/Sandbox manual MCP tokens.
- Two independent MCP clients supporting the selected `2026-07-28` authorization
  baseline or approved compatibility mode.

## 1. Static and migration gates

```bash
make spec-check
make lint
```

Run the migration proof against an empty disposable PostgreSQL database: upgrade to
head, inspect the three new tables/constraints, downgrade while empty, and upgrade
again. Separately prove downgrade refusal after inserting a grant lifecycle.

Expected outcome: no existing business or `mcp_access_token` column changes; all new
tenant keys and credential hashes are constrained as described in
[data-model.md](data-model.md).

## 2. Focused backend evidence

```bash
cd packages/reality-core
pytest -q \
  tests/test_mcp_oauth_service.py \
  tests/test_mcp_oauth_http.py \
  tests/test_mcp_oauth_migration.py \
  tests/test_mcp_http_runtime.py \
  tests/test_ai_mcp.py \
  tests/test_company_setup_api.py \
  tests/test_playground_security.py
```

Expected proof:

- discovery and challenges match [oauth.md](contracts/oauth.md);
- the selected MCP SDK/version proves the `2026-07-28` stateless resource-server and
  separate-issuer behavior before implementation proceeds;
- Authorization Code + PKCE rejects redirect, client, issuer, resource and replay
  mismatches;
- CIMD validation rejects SSRF and metadata substitution;
- one grant resolves one current user/client/company/tool authority per request;
- coarse requested scopes initially select every current eligible tool, permit
  individual deselection, and store only the exact approved nonempty subset;
- membership/account/company/grant revocation denies the next call;
- consent never confirms company creation or business execution;
- company setup retries produce one company and resume the same interaction;
- ready Sandboxes accept both interactive grants and manual MCP tokens while retaining
  the same tenant, exact-tool, proposal and explicit-confirmation controls;
- manual token behavior remains unchanged.

## 3. Browser and API journey

Run the frontend build, localization and focused browser contract:

```bash
make web-build
cd apps/web
npm run i18n:audit
node scripts/mcp-oauth-browser.mjs
```

Exercise these journeys in all four languages, light/dark themes, narrow/desktop
layouts and keyboard navigation:

1. Signed out → client connect → Reality login → one-company consent → allow → client
   read.
2. Multiple same-name companies → select exact company → prove other company absent.
3. Cancel at login, company selection and consent → zero grants.
4. No company → separately review/create/recover an ordinary company or Sandbox →
   resume consent and prove both ready company types are externally connectable.
5. Personal Connected Clients → revoke; Company Settings owner view → revoke another
   grant; manual token section remains distinct.
6. Lost response/reload/expired interaction/removed membership → truthful recovery or
   refusal without duplicate grant/company.

Expected outcome: no secret appears in URL, DOM snapshot, local/session storage,
clipboard fallback, console or error text. Browser code never handles a client redirect
URI directly.

## 4. Independent MCP client compatibility

For each of two supported clients:

1. Configure only the canonical Reality MCP URL.
2. Observe automatic protected-resource and issuer discovery.
3. Complete PKCE sign-in and exact-tool consent.
4. Call one permitted read and one ungranted tool.
5. Request added access and observe a fresh user decision.
6. Revoke the grant in Reality and prove the next request is denied.

Expected outcome: no Reality manual token instructions are needed; the permitted read
matches the canonical application result; denial is transport-level and reveals no
foreign data.

## 5. Confirmation and tenant business story

With a user grant that includes one read and one proposal tool:

1. Read company A.
2. Prepare one proposal.
3. Prove no business mutation occurred.
4. Open the existing Web proposal review as the same/currently authorized human.
5. Explicitly approve and verify the stored receipt and authoritative business read.
6. Repeat with a company-B identifier and prove not-found/refusal.

Expected outcome: login/consent grants access but never counts as proposal execution
confirmation. Source → Evidence → Reality traceability of the underlying business tool
is unchanged.

## 6. Full release gates

Run the complete required backend suite and repository gates from the normal project
environment, plus generated documentation checks if catalog inputs changed:

```bash
make test
make docs-generate
make docs-catalog-check
```

Record exact command, revision, date, pass/fail counts, skipped tests, both client
versions and screenshots in this feature's later review evidence. Do not mark tasks,
acceptance criteria or `docs/V0_CHECKLIST.md` complete while any required check is red.
