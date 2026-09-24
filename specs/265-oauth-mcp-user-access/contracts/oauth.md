# External OAuth and MCP Authorization Contract

## Canonical identifiers

- `resource`: exact configured public MCP URL, normalized once and compared exactly.
- `issuer`: exact configured public API/account authorization issuer.
- Production identifiers use HTTPS. Resource and issuer are distinct.

## Protected Resource Metadata

The MCP origin exposes the RFC 9728 path-specific well-known resource for its canonical
path and a root compatibility document. The payload includes:

```json
{
  "resource": "https://mcp.example.test/",
  "authorization_servers": ["https://api.example.test"],
  "scopes_supported": ["reality:read", "reality:propose", "reality:confirm"],
  "bearer_methods_supported": ["header"]
}
```

The actual values come from validated deployment configuration. Metadata never lists a
company, user, grant or tool allowlist.

## Authorization Server Metadata

The issuer exposes RFC 8414 metadata and compatible OIDC discovery. Required advertised
capabilities:

- authorization-code flow only for interactive MCP;
- PKCE `S256`;
- exact issuer, authorization, token and revocation endpoints;
- supported Reality scopes;
- RFC 9207 authorization-response issuer support;
- RFC 8707 resource indicators;
- pre-registered client support and CIMD support;
- public-client token endpoint authentication behavior;
- refresh token grant only when enabled.

Dynamic Client Registration is not exposed in the first release.

## Authorization request

`GET /oauth/authorize` accepts the standard fields:

```text
response_type=code
client_id=<pre-registered id or HTTPS CIMD URL>
redirect_uri=<exact registered URI>
code_challenge=<base64url SHA-256 challenge>
code_challenge_method=S256
resource=<exact MCP resource>
scope=<supported requested scopes>
state=<opaque client value>
```

The client requests only the coarse access classes represented by `scope`. The OAuth
request does not carry Reality tool names and a scope never expands automatically to all
tools in that class.

Validation occurs before browser interaction creation. On success, the issuer redirects
only to the fixed product route with an opaque Reality interaction ID. It never puts
client redirect targets, access tokens, codes or PKCE material into product Web storage.

After the user's explicit approve/deny decision, the issuer redirects to the previously
validated exact client redirect URI with standard success/error parameters, returned
`state`, and RFC 9207 `iss`. Approval returns a short-lived one-use code, never a token.

## Token endpoint

`POST /oauth/token` accepts form-encoded exchanges.

Authorization-code exchange requires:

```text
grant_type=authorization_code
code=<one-use code>
client_id=<same client>
redirect_uri=<same exact redirect>
code_verifier=<PKCE verifier>
resource=<same exact MCP resource>
```

Successful response follows OAuth bearer-token fields and may include a rotating
refresh token only when requested and allowed. Access is short-lived. Error responses
use standard OAuth codes and contain no account/company detail.

Refresh exchange, when enabled, requires the same client and resource and rotates the
refresh credential. Reuse terminates the credential family.

## Revocation endpoint

`POST /oauth/revoke` follows RFC 7009. A recognized access/refresh credential becomes
ineffective without revealing whether a supplied token existed. Revoking through
Reality Settings revokes the grant and therefore every related credential.

## Resource-server responses

- Missing, invalid, expired, revoked or wrong-resource credential: HTTP 401 plus
  `WWW-Authenticate: Bearer resource_metadata="<exact metadata URL>"`.
- Valid credential missing required scope: HTTP 403 plus Bearer
  `error="insufficient_scope"`, complete minimum `scope`, and `resource_metadata`.
- Valid scope but ungranted tool/current membership failure: deny before application
  dispatch using the least-disclosing protocol-compatible status.
- Authentication failures are HTTP failures, never successful MCP tool results.

## Client metadata validation

Pre-registered clients use server-owned exact metadata. CIMD clients use an HTTPS URL
with a non-root path and a document whose `client_id` exactly matches that URL. The
document provides a bounded name and exact redirect URI list. Fetching rejects userinfo,
non-HTTPS schemes, private/local/reserved IPs, DNS rebinding, unsafe redirects, excess
redirects, excess bytes and timeouts. Cached documents obey response cache policy but
are revalidated when security-relevant metadata changes.

## Scope and tool behavior

OAuth scopes are coarse stable access classes. Reality derives the currently eligible
tool choices from the canonical catalog and those requested scopes. Consent starts with
every current eligible tool selected, and the user may deselect individual tools before
approving a nonempty exact subset. The grant stores only that approved frozen subset.
Effective use requires both the scope matching the tool's current access class and the
exact tool grant; later catalog growth never expands it. `offline_access`, if supported,
is an authorization-server request and is never advertised as an MCP resource scope or
challenge requirement.
