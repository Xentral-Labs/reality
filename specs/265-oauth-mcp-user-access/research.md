# Phase 0 Research: OAuth MCP User Access

**Date**: 2026-09-24
**Scope**: Resolve protocol, authorization, persistence and repository-integration
unknowns before design.

## MCP protocol and resource-server role

**Decision**: Target MCP specification `2026-07-28`. Keep the dedicated Reality MCP
runtime as a stateless OAuth resource server and the existing API/account runtime as a
separate logical authorization server. Authentication context is derived independently
on every HTTP request; there is no authoritative MCP transport session.

**Rationale**: The current MCP release removed protocol sessions and aligns remote MCP
authorization with OAuth resource-server discovery. The Python SDK recommends new
servers use its token-verifier/resource-server boundary instead of embedding the legacy
full authorization-server provider inside MCP. Reality's API already owns human login,
membership and company setup, while MCP must remain a separate adapter.

**Alternatives considered**:

- Make MCP itself the authorization server: rejected because it duplicates account and
  consent authority and couples interactive login to the machine runtime.
- Deploy a new commercial authorization product first: rejected as the smallest first
  increment because company/tool consent and current-membership checks remain Reality
  application policy. A later deployment may externalize generic protocol functions
  without changing these contracts.
- Reuse the Web cookie at MCP: rejected because it leaks browser-session authority
  across origins and is not interoperable MCP authorization.

**Primary sources**: [MCP authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization), [MCP 2026-07-28 release](https://blog.modelcontextprotocol.io/posts/2026-07-28/), [Python SDK authorization](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/run/authorization.md).

## Discovery and HTTP challenges

**Decision**: Publish RFC 9728 Protected Resource Metadata at the canonical
path-specific well-known URL and at the root compatibility URL. Advertise the exact
canonical MCP resource and separate authorization issuer. Missing/invalid credentials
return HTTP 401 with `WWW-Authenticate` and `resource_metadata`; valid but insufficient
credentials return HTTP 403 with `insufficient_scope`, complete required scopes and
the same metadata reference.

**Rationale**: Current clients discover the authorization server from the protected
resource, and the MCP specification requires transport-level failures rather than tool
results for authorization failures.

**Alternatives considered**: A tool-level authentication error and a static setup URL
were rejected because clients cannot start or repair authorization interoperably.

**Primary sources**: [MCP authorization-server discovery](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/authorization-server-discovery), [RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728).

## Human authorization and token targeting

**Decision**: Use Authorization Code with mandatory PKCE S256, exact redirect matching,
client `state`, RFC 9207 authorization-response issuer, and RFC 8707 `resource` on both
authorization and token requests. Credentials are valid only for the exact Reality MCP
resource.

**Rationale**: These controls prevent intercepted-code redemption, replay,
authorization-server mix-up and accepting a token issued for a different API.

**Alternatives considered**: Implicit flow, password exchange and bearer credentials
without audience/resource restriction were rejected as incompatible or unsafe for
public interactive clients.

**Primary sources**: [MCP security considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations), [RFC 8707](https://datatracker.ietf.org/doc/html/rfc8707), [RFC 9207](https://datatracker.ietf.org/doc/html/rfc9207).

## Client registration compatibility

**Decision**: Support pre-registration for controlled clients and Client ID Metadata
Documents for open current clients. Do not implement Dynamic Client Registration in
the first release. Validate CIMD over HTTPS with exact document/client/redirect matches
and an SSRF-safe bounded fetcher.

**Rationale**: MCP `2026-07-28` deprecates DCR and prefers established registration or
CIMD. A database-backed public DCR endpoint would add client lifecycle and impersonation
surface without proving a required supported client.

**Alternatives considered**:

- DCR as primary: rejected because it is deprecated and substantially expands attack
  surface.
- Manual client IDs only: rejected because it does not meet open-client
  interoperability.
- Trust arbitrary client metadata URLs: rejected due redirect substitution and SSRF.

**Primary source**: [MCP client registration](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration).

## Credential form, renewal and revocation

**Decision**: Issue short-lived opaque access tokens and optional rotating refresh
tokens, storing only SHA-256 hashes. Every request resolves the access record and grant
in PostgreSQL. Expose RFC 7009 revocation. Refresh-token reuse revokes its credential
family.

**Rationale**: Reality already operates hashed opaque browser and MCP credentials.
Opaque lookup provides immediate grant revocation and avoids adding signing-key/JWKS
operations while every request must query current membership anyway. Rotating refresh
supports interactive clients without long-lived bearer access.

**Alternatives considered**:

- Self-contained JWT access tokens: valid but does not remove the required live grant
  and membership lookup; adds signing-key/JWKS lifecycle.
- Long-lived access tokens: rejected because user/membership/grant revocation must be
  promptly effective.
- No renewal: simpler, but would force frequent browser interaction. Renewal remains
  optional to clients and is issued only when explicitly requested/supported.

**Primary sources**: [MCP refresh tokens](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization#refresh-tokens), [RFC 7009](https://datatracker.ietf.org/doc/html/rfc7009).

## Tenant and effective authority

**Decision**: One interactive grant binds one user, client and ready company, including
a Sandbox. Each call intersects current account eligibility, active membership and role,
unarchived company, unrevoked grant, access scopes, exact tool allowlist and
operation-specific service policy. Company never comes from a tool argument.

**Rationale**: This preserves the repository's tenant invariant, makes membership
removal immediately effective and avoids confused-deputy behavior. A distinct grant is
required for a company switch.

**Alternatives considered**:

- Multi-company access token: rejected as a new cross-company product surface.
- Store only tenant in token subject: rejected because it loses user/client/grant
  attribution and current membership authority.
- Use browser's current-company preference: rejected because mutable UI state is not
  authorization.

## Exact tool selection

**Decision**: MCP clients request only coarse OAuth access-class scopes. Reality derives
eligible tools from those scopes and its canonical catalog, initially selects every
eligible current tool, lets the user deselect individual tools, and stores the exact
nonempty subset approved by the user.

**Rationale**: Standard OAuth/MCP authorization requests do not carry Reality-specific
tool names. Preselection reduces setup friction for a large catalog while the visible
exact list and ability to deselect preserve an explicit user decision. The stored list
is frozen, so later catalog growth never expands an existing grant.

**Alternatives considered**: Tool-name scopes would make a volatile catalog part of
the stable OAuth vocabulary; a custom authorization parameter would not interoperate
with ordinary MCP clients; an initially empty selection was rejected as unnecessary
friction because proposal and explicit-confirmation boundaries remain authoritative.

## Company creation during consent

**Decision**: Browser consent may reuse `company_setup.options`, `create_company`,
`read_request` and `retry_request`. Consent itself never calls creation. After separate
explicit confirmation and readiness, any canonical company type, including a Sandbox,
may become the grant company. Interactive grants and manual tokens use the same Sandbox
eligibility rule.

**Rationale**: The existing service already owns eligibility, confirmation,
idempotency, owner membership, initialization and recovery. Sandbox isolation and the
shared proposal/confirmation boundary make it a useful full MCP test environment; a
credential-kind-specific prohibition would create inconsistent behavior.

**Alternatives considered**: A company-creation MCP tool, direct tenant/membership
write, or treating consent as creation confirmation were rejected as parallel mutation
paths and violations of the confirmation contract.

## Internal principal and shared dispatch

**Decision**: Introduce an immutable transport-neutral `MCPPrincipal` carrying
credential kind, credential/grant ID, user if interactive, tenant, client, scopes and
exact tools. The MCP handler obtains it only from the verified access context and
forwards it through the canonical dispatcher. Human identity is injected internally
for attribution/confirmation checks; no private actor argument becomes client input.

**Rationale**: Current code overloads MCP SDK `subject` with tenant ID and cannot
distinguish user, client or manual integration. A richer verified principal is needed
without changing business tool schemas.

**Alternatives considered**: Add `tenant_id`/`user_id` to each tool schema or infer
identity from proposal input; both were rejected as forgeable and divergent.
