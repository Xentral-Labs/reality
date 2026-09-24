# Browser Interaction and Grant Management Contract

All `/api/oauth/...` routes require the existing Reality HttpOnly browser session. They
never accept a bearer credential intended for MCP and never return authorization codes,
access tokens, refresh tokens, PKCE verifiers or arbitrary redirect URLs.

## Read authorization interaction

`GET /api/oauth/interactions/{interaction_id}`

Returns a bounded consent view:

```json
{
  "id": "oai_opaque",
  "client": {
    "id": "https://client.example/mcp.json",
    "name": "Example MCP Client",
    "uri": "https://client.example"
  },
  "requested_scopes": ["reality:read"],
  "eligible_tools": [
    {"name": "inventory_read", "label": "Inventory", "access": "read"}
  ],
  "companies": [
    {"id": "ten_opaque", "name": "Example GmbH", "role": "owner", "ready": true}
  ],
  "company_setup": {
    "eligible": true,
    "external_mcp_requires_business_company": false
  },
  "expires_at": "2026-09-24T12:00:00Z",
  "status": "pending"
}
```

Only current active memberships are returned. Company display names are explanatory;
opaque IDs select the company. Ready Sandboxes and ready ordinary companies are both
eligible MCP grant targets.

## Approve

`POST /api/oauth/interactions/{interaction_id}/approve`

```json
{
  "company_id": "ten_opaque",
  "allowed_tools": ["inventory_read"],
  "confirmed": true
}
```

Approval requires `confirmed=true`, a pending unexpired interaction, the same current
browser user, an active membership in the ready unarchived company, and a nonempty
exact-tool subset chosen from `eligible_tools`. Every current eligible tool starts
selected from the client's coarse requested scopes and current catalog; the user may
deselect individual tools. The service revalidates client metadata, redirect, scopes
and the exact selected tools at commit.

The response contains only a fixed same-origin completion instruction. The API performs
the final redirect or supplies a server-owned completion path; it never returns the
client's arbitrary redirect URI for browser JavaScript to navigate.

Approval is single-use and creates no business mutation.

## Deny

`POST /api/oauth/interactions/{interaction_id}/deny`

```json
{"confirmed": true}
```

Denial terminally records `access_denied`, creates no grant, and returns only the fixed
completion instruction.

## Company setup reuse

The authorization page calls the existing contracts unchanged:

- `GET /api/company-setup/options`
- `POST /api/company-setup`
- `GET /api/company-setup/requests/{request_key}`
- `POST /api/company-setup/requests/{request_key}/retry`

Its wrapper retains the opaque interaction ID and resumes consent with the exact ready
tenant from the setup result. Company creation has its own explicit review and
`confirmed=true`; consent approval is a later separate request. Any ready canonical
company type, including a Sandbox, may become the eventual MCP grant target under the
same tenant, tool, proposal and explicit-confirmation controls.

## Personal grant inventory

`GET /api/auth/mcp-grants`

Lists grants authorized by the current user across companies, including grant ID,
client display identity, company ID/name, exact tools/access classes, creation,
last-use and effective/revoked state plus a safe reason. It contains no credential
prefix or secret.

`POST /api/auth/mcp-grants/{grant_id}/revoke`

```json
{"confirmed": true}
```

Only the authorizing user can use this route. It revokes the grant and related
credentials idempotently without affecting other clients/companies.

## Company-owner grant inventory

`GET /api/tenants/{tenant_id}/settings/mcp/grants`

Lists interactive grants for the current company after owner authorization. It includes
the authorizing user's safe display identity and otherwise matches the personal view.

`POST /api/tenants/{tenant_id}/settings/mcp/grants/{grant_id}/revoke`

```json
{"confirmed": true}
```

Requires current company owner authority and exact tenant/grant match. Cross-tenant
grants behave as not found.

Existing manual routes under `/settings/mcp/tokens` remain unchanged and are presented
separately as “Manual API tokens”.
