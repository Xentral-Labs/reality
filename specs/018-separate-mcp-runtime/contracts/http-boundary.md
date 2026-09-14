# Contract: Dedicated HTTP MCP Boundary

## Routes

| Route | Authentication | Purpose |
|---|---|---|
| `/` | MCP bearer credential required | Streamable HTTP MCP protocol |
| `/healthz` | None | Process liveness only |
| `/readyz` | None | Bounded dependency and registry readiness |

Health responses contain no tenant, token, tool arguments/results, business payloads,
database URL, or raw exception detail.

## Authentication and tenant authority

1. Bearer clear text is hashed and compared to an active existing MCPAccessToken.
2. Verification returns the token record ID, scopes, and exactly one tenant subject.
3. The subject supplies tenant authority for every tool call.
4. Tool arguments cannot accept or override tenant identity.
5. The current allowlist is enforced for each protected call.
6. Revocation or allowlist reduction affects subsequent protected calls without an
   unspecified cache delay.

## Tool behavior

- Tool list and schemas derive from the canonical registry.
- Read tools invoke shared application reads.
- Propose tools create only ChangeProposal records.
- Confirm tools preserve their existing explicit approval input and authorization
  semantics; feature 018 does not grant automated approval.
- Cross-tenant record references use existing not-found behavior.
- Structured results preserve opaque IDs and Source/Evidence/Reality trace links.

## HTTP outcome classes

- Missing/invalid credential: authentication failure without tenant disclosure.
- Valid credential, forbidden tool: authorization failure without executing handler.
- Valid allowed call: protocol success containing canonical structured result.
- Application validation/not-found: bounded tool error preserving existing semantics.
- Dependency unavailable: bounded service failure and not-ready runtime; no false
  success.

## Removed surface

After cutover:

- Web/API does not mount `/mcp/` or own MCP session lifespan.
- No stdio transport, fixed-tenant MCP server, `reality mcp` CLI command, or module
  subprocess contract remains.
- Internal Copilot is not an MCP transport client; it uses the canonical registry and
  shared handlers directly.
