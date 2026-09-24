# Connect an MCP client

Reality exposes tenant-scoped business tools to compatible external agents through authenticated
Streamable HTTP. Use this guide to connect one client with only the capabilities it needs.

## One human setup, then the agent works

The recommended connection starts with a short, one-time browser setup and authorization by a
person. The person signs in, creates or selects the company, chooses the exact tool allowlist, and
approves the client. The client then exchanges the authorization code for a tenant-scoped access and
refresh token. The agent uses those tokens directly; it does not receive the person's browser
session or password.

```text
Human in the browser, once:
account → company → tool allowlist → OAuth approval

Agent afterwards:
MCP endpoint + access token → discover and use permitted tools
```

An agent or integrating system must not automate signup, email verification, or human approval. If
no person has completed authorization, open the client's OAuth login flow and ask the person to
finish it in the browser. This is the same starting contract for every third-party agent.

## What an agent can do

An authorized agent can inspect orders and commitments, read inventory, find fulfillment blockers,
explain exceptions through their evidence, and review proposals. It can also prepare controlled
business changes such as a reservation or movement. Read calls run immediately. A mutation creates a
proposal; it does not change business state until a person explicitly approves it. After execution,
the agent should re-read the declared projection or status tool to verify the result.

See [Agent capabilities](/tool-usage/#choosing-a-tool) for selection and verification guidance and
the generated [Tool Usage reference](../tool-usage/commands) for current names and parameters.

## Prerequisites

- A person has completed signup and email verification in the Reality browser application.
- That person has created or selected the company the agent should use.
- A compatible MCP client that supports OAuth authorization-code flow with PKCE and Streamable HTTP.
- An HTTPS redirect URI registered for the client. Reality also supports bounded HTTPS client
  metadata documents (CIMD) when a client is not pre-registered.

## 1. Find the endpoint

Open **Company settings → Agents → MCP Server** and copy the displayed endpoint. Deployments publish
this value as `MCP_URL`. Production endpoints use HTTPS and the origin root, for example:

```text
https://mcp.example.com/
```

Do not append `/mcp` unless the displayed deployment URL includes it. The displayed URL is the
authority.

## 2. Authorize the client

Start the client's connection flow at the advertised MCP endpoint. Reality redirects the browser to
the sign-in and consent screen. Select one ready company and the smallest tool allowlist that
supports the client's job, then confirm. A read-only analyst normally needs discovery and relevant
read tools, not every current and future tool.

## 3. Configure the client

Client interfaces differ, but the connection contract is the same:

```text
Transport: Streamable HTTP
URL:       <the displayed MCP_URL>
Auth:      OAuth 2.1 authorization code + PKCE
```

The client stores access and refresh tokens in its secure credential storage. Do not put tokens in a
repository, prompt, screenshot, shared document, or source payload.

## 4. Verify a first read

Start with a read-only request. Ask the client to call `business_records_discover` for a known
business reference, or describe `inventory_read` with `capability_describe` before reading
inventory.

A successful connection proves that the token, tenant, endpoint, and selected tool work together. An
empty result does not prove that the company has no relevant record or issue; follow the tool's data
basis, freshness, limitations, and next-step guidance.

## 5. Understand governed changes

Mutation tools exposed to an agent are proposal tools. The safe sequence is:

```text
inspect → propose → human approval → execute → verify
```

Review the exact intended effect before approval. Permission to propose is not proof of approval,
execution, fulfillment, delivery, or settlement. After execution, use the capability's declared
verification read rather than trusting a success sentence alone.

## Troubleshooting

- **Unauthorized**: check the exact endpoint and bearer token; create a replacement if the clear
  token was lost.
- **Tool forbidden**: add the required tool deliberately or use a separate token with the
  appropriate tool allowlist.
- **Client asks for OAuth**: continue through the browser flow; OAuth is the supported interactive
  connection path.
- **Empty result**: verify the business reference, tenant, source coverage, filters, and freshness.
- **Unknown execution result**: inspect the proposal execution status and do not retry blindly.

## Revoke access

Return to **Company settings → Agents → MCP Server** and revoke the named token when a client is no
longer used, a device is lost, or a credential may have leaked. Revocation blocks subsequent calls;
create a separate replacement token instead of sharing one token between clients.

## Current authentication boundary

Reality provides OAuth authorization-code flow with S256 PKCE, exact resource and redirect
validation, browser consent, tenant-scoped tool grants, access-token expiry, refresh-token rotation,
and revocation. The resulting tenant-scoped MCP access token is the agent credential. OAuth is a
permanent part of the MCP product boundary. Client registration is explicit through
`MCP_OAUTH_CLIENTS` or a bounded HTTPS CIMD document; there is no open registration endpoint.
Company creation remains a human-confirmed browser operation and is never performed by an agent
without that consent.

## Read response migration (contract v2)

`business_records_discover`, `inventory_read`, `commitments_list`, `fulfillment_queue`,
`fulfillment_blockers`, and `item_supply_demand` now return
`{records, next_cursor, has_more, metadata}` by default. Read the `records` array and pass
`next_cursor` with the same tool and filters until `has_more` is false. `limit` is 1–100 (default
25). A cursor cannot move between tenants or filters. Traversal reads live retained records, not a
frozen snapshot or proof that all upstream data has arrived. For a staged client migration,
explicitly pass `response_format: "legacy"`; legacy operational reads may refresh and commit
projection caches. Page mode does not write business records or projection caches. Authentication
may independently persist token-use telemetry.

`finance_balances` returns `{balances, metadata}` with separate currency entries containing
`currency`, `receivables`, and `payables`. It never converts or totals currencies, and these
positions are not net revenue or profit. This corrected finance shape has no legacy mode. Ledger
discovery exposes `debit_credit`.

Inventory defaults to explicitly labelled item aggregates. Request `view: "location"` or
`location_id` for location stock, optionally narrowed by `item_id`. Operational quantities include
recorded units; missing or mismatching units do not trigger conversion. `order_explain` includes
retained fulfilled and cancelled orders via document or delivery commitment IDs, without
reconstructing arbitrary past states.

Metadata identifies the tenant, filters, UTC observation time, known projection version and observed
local event sequence. Upstream freshness remains `unknown`. The sequence is not a snapshot
identifier. Order explanations and finance reads also avoid business/cache writes and commits.
Business actions retain their existing confirmation requirements.

For what an agent should do with these tools per business area, and what stays with a person, read
the [Agent Playbooks](../agent-playbooks/).
