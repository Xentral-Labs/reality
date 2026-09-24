# Implementation Plan: OAuth MCP User Access

**Review state**: Architecture and security direction approved for implementation on
2026-09-24. Reviewer-owned final security checklist verification remains a release
gate.

**Branch**: `[265-oauth-mcp-user-access]` | **Date**: 2026-09-24 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Add standards-based interactive MCP authorization without replacing the existing
manual integration-token path. The dedicated MCP runtime remains a stateless OAuth
resource server. The existing API/account runtime becomes the authorization boundary
because it already owns Reality login, company membership, consent UI hosting and
confirmed company setup. It issues short-lived opaque, resource-bound credentials
after Authorization Code + PKCE S256 and stores only hashes.

One revocable grant binds one user, one client and one ready company to a
frozen exact-tool allowlist and coarse read/propose/confirm scopes. Every MCP request
resolves a transport-neutral principal and rechecks the grant, account, membership,
company, resource, scope and tool before the canonical application-tool dispatcher.
Existing `MCPAccessToken` records continue unchanged for unattended integrations.

The first implementation targets MCP `2026-07-28`, pre-registered clients and Client
ID Metadata Documents (CIMD). Dynamic Client Registration is not added because the
current MCP specification deprecates it. Browser consent may call the existing
account-scoped company setup APIs. Every ready company type, including a Sandbox, can
be bound to an external MCP grant through either interactive or manual credentials.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript where frontend is in scope
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, React/Vite, MCP Python SDK; existing `cryptography` and `httpx` only where protocol validation requires them
**Storage**: PostgreSQL; immutable object storage only for proven source binaries
**Testing**: pytest business stories/integration/unit; frontend build and focused UI tests
**Project Type**: backend services/API/CLI plus independent frontend
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope
**Scale/Scope**: One MCP resource origin, one authorization issuer, one company per grant, exact current tool catalog, bounded short-lived authorization interactions and credentials, existing four product languages; no upstream connector OAuth and no cross-company grant

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Authorization creates no business Evidence or Reality. Authorized tools retain their existing Source → Evidence → Reality paths; see [data-model.md](data-model.md). | PASS |
| Reality owns operational state | Grants describe access only and never add document status or operational state. Proposal/execution continues through existing Reality services. | PASS |
| Proven schema only | Three security/account tables are required for explicit consent, single-use PKCE exchange, hashed short-lived/renewable credentials and immediate revocation. No business table changes; field proof is in [data-model.md](data-model.md). | PASS |
| Tenant + shared service boundaries | Tenant comes only from the verified grant/manual credential. Every interactive call rechecks active membership and dispatches the same application tool. Adapters perform no ORM business write. | PASS |
| Spec/test traceability | [Test Strategy and Traceability](#test-strategy-and-traceability) maps all FR/DR groups to executable proof, with security tests first. | PASS |
| Explainable web behavior | Consent shows client, account, one company and exact access; Personal/Company Settings show grant lifecycle without secrets. Company creation reuses its existing explained review/recovery. | PASS |
| Received values not recomputed | N/A to access control. No source-stated business value is recorded or derived by authorization. | PASS |
| Smallest coherent design | Reuses login, membership, company setup, security audit, tool catalog and manual tokens. It adds no IdP, broker, DCR registry, JWT authority, MCP session store or parallel tool path. | PASS |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/domain/       # pure rules, if needed
packages/reality-core/src/reality/services/     # application behavior
packages/reality-core/src/reality/tools/        # shared agent/CLI tools
packages/reality-core/src/reality/web/          # transport only
packages/reality-core/tests/                    # unit, service, story, adapter proof
apps/web/src/                     # presentation only
```

**Files/layers affected**:

```text
packages/reality-core/src/reality/db/mcp_authorization.py       # new account/security models
packages/reality-core/src/reality/db/core.py                    # import model metadata only
packages/reality-core/src/reality/services/mcp_authorization.py # grants, PKCE exchange, credentials, principal resolution
packages/reality-core/src/reality/mcp/principal.py              # immutable transport-neutral MCP principal
packages/reality-core/src/reality/mcp/auth.py                   # composite manual/interactive verifier
packages/reality-core/src/reality/mcp/server.py                 # separate issuer, challenge and principal-aware dispatch
packages/reality-core/src/reality/mcp/app.py                    # protected-resource metadata routes
packages/reality-core/src/reality/mcp/config.py                 # canonical resource and issuer configuration
packages/reality-core/src/reality/mcp/catalog.py                # server-owned principal forwarding only
packages/reality-core/src/reality/web/mcp_authorization.py      # OAuth and browser-interaction HTTP adapters
packages/reality-core/src/reality/web/app.py                    # router/public-boundary registration
packages/reality-core/src/reality/web/api.py                    # no OAuth logic; existing manual-token routes retained
packages/reality-core/pyproject.toml                            # proven MCP SDK compatibility/version bound
packages/reality-core/migrations/versions/0094_mcp_user_authorization.py
packages/reality-core/tests/test_mcp_oauth_service.py
packages/reality-core/tests/test_mcp_oauth_http.py
packages/reality-core/tests/test_mcp_oauth_migration.py
packages/reality-core/tests/test_mcp_http_runtime.py             # challenge/discovery/manual regression
packages/reality-core/tests/test_ai_mcp.py                       # principal/tool/proposal/manual regression
packages/reality-core/tests/test_company_setup_api.py            # setup resume from consent
apps/web/src/OAuthAuthorization.tsx                              # login/consent/company selection wrapper
apps/web/src/Auth.tsx                                            # explicit authorization route handling
apps/web/src/entryRouting.ts                                     # opaque interaction return only
apps/web/src/api.ts                                              # typed interaction/grant client
apps/web/src/unified/MCPAccess.tsx                               # split manual tokens and connected clients
apps/web/src/unified/SettingsPage.tsx                            # personal/company grant management entry
apps/web/src/localization.tsx                                    # four-language copy
apps/web/scripts/mcp-oauth-browser.mjs                           # responsive/recovery/security UI journey
docs/features/mcp-user-authorization.md                          # durable authorization contract
docs/WEB_SPEC.md, docs/ARCHITECTURE.md, docs/DATA_MODEL.md,
docs/TEST_STRATEGY.md                                            # reconciled long-lived contracts
```

Dependency direction remains Web/OAuth and MCP adapters → authorization/application
services → account/security persistence. Only existing application tools reach business
services and tenant business tables.

## Design

### Reality flow

Authentication and consent are outside the business Source → Evidence → Reality chain.
The shortest access path is:

```text
AppUser → active TenantMembership → Tenant
      └→ MCPClientGrant → MCPUserCredential
MCPAuthorizationInteraction ──on approval──> MCPClientGrant
```

`MCPClientGrant` names its user, client and company once; it does not duplicate
Document, SourceRecord or business-record links. `SecurityAuditEvent` refers to the
grant/credential by opaque subject identity and contains bounded redacted metadata.
After authorization, the existing application tool owns any normal business flow and
preserves its established provenance.

### Service and adapter flow

1. An unauthenticated client calls the canonical MCP resource URL. The MCP runtime
   returns HTTP 401 with RFC 9728 metadata discovery, never a successful tool error.
2. The client discovers the API/account authorization issuer and starts Authorization
   Code + PKCE S256 with the exact MCP resource indicator.
3. The API validates the request and either a pre-registered client or an HTTPS CIMD
   document. It creates a bounded single-use authorization interaction and redirects
   the browser only to the product's fixed authorization route with the opaque
   interaction ID.
4. Product Web uses the existing HttpOnly Reality session to read the interaction.
   The client has requested only coarse OAuth scopes. The user selects one active ready
   company and reviews every current tool in those scopes as initially selected, with
   the option to deselect individual tools before approval. Alternatively, the user
   enters the canonical confirmed company-setup journey and resumes once the company,
   including a Sandbox, is ready.
5. Approval rechecks client, redirect, resource, account, membership, company and tool
   catalog, creates/replaces the explicit grant, and turns the interaction into a
   short-lived one-use code. Denial creates no grant.
6. The client exchanges the code using its PKCE verifier and exact redirect/resource.
   Reality stores only access/refresh hashes. Refresh rotates the credential family;
   reuse revokes the family. RFC 7009 revocation terminates the grant credentials.
7. Each MCP request uses the composite verifier. Manual `ros_mcp_` tokens retain their
   current verifier. Interactive credentials resolve a fresh `MCPPrincipal` and recheck
   current account eligibility, active membership, unarchived ready company, grant,
   resource, scopes and exact tool.
8. `RealityServer.call_tool`/catalog dispatch accepts only the server-owned principal.
   It passes the principal's tenant to the existing dispatcher and the verified user
   identity through an internal caller context for attribution. No tool input may set
   or override either value. Read/propose/confirm semantics remain unchanged.
9. Personal Settings lists a user's own grants; Company Settings owners list and revoke
   grants for that company. Existing manual-token administration remains separate.

### Data and migration impact

Migration `0094_mcp_user_authorization` adds only the three account/security models
defined in [data-model.md](data-model.md): `mcp_client_grant`,
`mcp_authorization_interaction`, and `mcp_user_credential`. They are necessary to
prove explicit grant identity, PKCE single use, lossless protocol retry/rejection,
hashed credential handling, rotation and immediate revocation. They are not business
tables and never hold business payloads.

No existing row is backfilled. `mcp_access_token` remains unchanged. The migration is
additive and downgrade is refused while any new authorization row exists; deleting
active security authority during rollback would silently invalidate connections and
erase audit-relevant lifecycle state. The application may roll back to the prior
release only before interactive grants are enabled or after an explicit reviewed
revocation/export cleanup.

### Failure, security, and tenant behavior

- Canonical MCP resource and authorization issuer URLs are explicit configuration;
  production requires HTTPS and exact origin/path comparison.
- Protected Resource Metadata is published at the RFC 9728 path-specific location and
  root compatibility location. The AS publishes RFC 8414 and OIDC discovery metadata
  with PKCE S256, RFC 9207 issuer response support, resource indicators and CIMD.
- Missing/invalid credentials return 401; a valid credential missing authorization
  returns 403 with all required scopes. Challenges contain no tenant or user detail.
- Access tokens are opaque, hashed, audience-bound and expire after 15 minutes.
  Optional renewable access uses rotating, hashed refresh material expiring after at
  most 30 days; no browser or business tool receives it. Authorization interactions
  and codes expire after 10 minutes. Production may configure shorter, never longer,
  lifetimes; tests and metadata pin the effective values.
- CIMD fetches allow HTTPS only, reject private/local/reserved targets and redirects to
  them, enforce DNS/IP checks on every hop, and cap redirects, bytes and time. Client
  ID, document ID and exact redirect URI must match. Pre-registration is supported for
  controlled clients; DCR is deliberately absent.
- Authorization interactions/codes are short-lived, single-use and transactionally
  consumed. Redirect URIs are exact matches. `state` is returned unchanged only to the
  previously validated redirect. Codes are bound to client, redirect, resource and
  PKCE challenge.
- Grant approval and token exchange lock the relevant rows. Replay, refresh reuse,
  revocation and concurrent membership loss fail atomically with no partial grant or
  business effect.
- The client-selected company is never accepted by an MCP tool. Cross-tenant object
  access preserves current not-found/refusal behavior.
- Current membership/account/company checks occur on every interactive call, so
  disablement is effective before token expiry. Manual tokens intentionally retain
  their existing company-owned semantics.
- OAuth consent is not company-creation confirmation and never approves a business
  proposal. Canonical company setup requires its existing explicit `confirmed=true`
  request. MCP `confirm` access still invokes the existing fresh human decision rules.
- Ready Sandbox companies use the same MCP credential paths and effective-authority
  checks as ordinary companies. Interactive and manual access both retain tenant
  isolation, exact-tool authority, proposal-first mutation and explicit confirmation;
  Sandbox status neither broadens nor blocks those controls.
- Creating a new authorization interaction performs a bounded opportunistic retention
  sweep in the same service: at most 500 terminal interactions older than 7 days and
  500 terminal credentials older than 90 days. Cleanup is hygiene only, never required
  for authorization correctness, and no timer or queue is introduced.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-003, FR-021–FR-022 | HTTP/conformance | `test_mcp_oauth_http.py`: RFC 9728/8414/OIDC discovery, 401/403 challenges, PKCE S256, resource and issuer validation, pre-registration and CIMD security | Current endpoint only accepts manual bearer tokens and advertises itself as issuer |
| FR-004–FR-006 | Service/API/browser | authorization interaction read/approve/deny; same-name and multiple-company browser journeys | No consent interaction or company-bound user grant exists |
| FR-007–FR-010 | Service/adapter | active/removed membership, disabled account, archived/wrong tenant, wrong client/resource/scope/tool, catalog growth | Current verifier knows only tenant token and tool scope |
| FR-011, FR-015 | Service/HTTP | access expiry, refresh rotation/reuse, grant and RFC 7009 revocation, immediate denial | No interactive credential lifecycle exists |
| FR-012 | Business story | read → proposal → Web review → explicit execution with verified actor; consent-only zero effects | MCP has no user principal and consent flow |
| FR-013–FR-014 | Service/API/browser | existing setup options/create/read/retry from an interaction; cancel/lost response; ready ordinary and Sandbox grants | Setup currently always returns to normal app entry |
| FR-016 | Service/browser | second company produces a distinct grant/credential; first remains immutable | No interactive company grant exists |
| FR-017 | Regression | existing `test_ai_mcp.py`, `test_mcp_http_runtime.py`, ordinary/Sandbox parity and new mixed inventory view | Management has only manual credentials |
| FR-018 | Adapter/contract | interactive/manual principals dispatch identical tools; no direct ORM business writes | Dispatcher accepts tenant only, not a verified principal |
| FR-019 | Service/API | bounded lifecycle/denial audits and management results contain no clear code/access/refresh token or business payload | No grant audit exists |
| FR-020 | HTTP/browser | cancel, expiry, lost callback, unsupported client, AS outage, interrupted setup and retry | No interactive failure journey exists |
| DR-001–DR-005 | Migration/domain/repository | migration schema review, tenant-key catalog, business-table diff guard, provenance and proposal regression | New security model absent |

Tests are added before implementation where practical: migration/model constraints,
service state machine and HTTP conformance first; then adapters and browser journeys.
Run focused failures before code, followed by the complete PostgreSQL backend suite,
Ruff, migration up/down/up on an empty database, frontend build/format/i18n audit,
browser layouts, `make spec-check`, `make docs-generate`, and
`make docs-catalog-check` when catalog-derived documentation inputs change.

## Rollout and Rollback

1. Ship additive migration, inactive service code and configuration validation. Manual
   tokens remain the only working path.
2. Deploy API/account authorization endpoints and discovery metadata as a permanent
   MCP boundary. Verify issuer, resource, PKCE, CIMD and company/setup journeys
   before release; there is no runtime disable switch.
3. Deploy the matching MCP resource-server release, then advertise the authorization
   issuer and enable supported clients. API and MCP must run the same core revision.
4. Add connected-client management and security telemetry: authorization starts,
   approvals/denials, exchanges, refresh reuse, credential/grant revocations and
   refusal codes only—never query parameters, tokens, PKCE verifiers or payloads.
5. Verify two independent current clients and the existing manual-token suite in the
   target environment before documenting interactive connection as available.

Application rollback disables new interactive authorization and restores the previous
MCP release while leaving additive tables intact. Already issued interactive tokens
must be revoked/disabled before rollback because the old MCP runtime cannot honor their
grant lifecycle. Manual tokens remain available throughout. Database downgrade is not
part of routine rollback once authorization rows exist.

## Review Risks

- Confusing OAuth consent with Reality's separate company/business confirmation would
  violate the product's human-decision boundary.
- Incorrect `resource`, issuer, redirect or CIMD validation creates token theft,
  impersonation, mix-up or SSRF risk; protocol conformance is a release blocker.
- Treating an access-token claim or tool argument as tenant authority could disclose
  another company. Live grant/membership resolution is mandatory on every call.
- The current dispatcher carries only tenant identity. Actor propagation must be
  server-owned and must not make private confirming-user fields client-controlled.
- Removing the former Sandbox credential prohibition must not weaken tenant, user,
  exact-tool, proposal or explicit-confirmation checks, and both credential kinds must
  behave consistently for a ready Sandbox.
- Per-request `last_used_at` writes may create avoidable contention. Update it in a
  bounded best-effort cadence while preserving immediate security checks; lifecycle
  audit rows remain event-based rather than one row per tool call.
- MCP Python SDK support for the 2026-07-28 stateless protocol and separate issuer must
  be proven by a focused executable spike before implementation dependencies are
  upgraded and pinned in `packages/reality-core/pyproject.toml`; do not reintroduce a
  stateful MCP-session authority as a compatibility workaround.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Post-Design Constitution Check

All eight blocking rows remain PASS after the Phase 1 model and contracts. The design
adds no business schema, parallel tool/service, Sandbox exception, stored derivation or
document-owned operational state. The only new persistence is bounded account/security
authority proven directly by FR-004–FR-011, FR-015–FR-019 and the protocol contracts.
