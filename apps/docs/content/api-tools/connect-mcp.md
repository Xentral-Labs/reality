# Connect an MCP client

Reality exposes tenant-scoped business tools to compatible external agents through authenticated
Streamable HTTP. Use this guide to connect one client with only the capabilities it needs.

## One human setup, then the agent works

The current connection starts with a short, one-time browser setup by a person. The person creates
and verifies a Reality account, creates or selects the company, and issues a tenant-scoped MCP
access token for the client. After that handoff, the agent uses the MCP endpoint and token directly;
it does not need the person's browser session or password.

```text
Human in the browser, once:
account → email verification → company → scoped MCP token

Agent afterwards:
MCP endpoint + token → discover and use permitted tools
```

An agent or integrating system must not automate signup, email verification, or an interactive
login. If no person has completed the browser setup, ask one to do so and provide the displayed MCP
endpoint and the token shown once. This is the same starting contract for every third-party agent or
knowledge system; there is no product-specific provisioning path today.

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
- Company-owner access to **Company settings → Agents → MCP Server** for token management.
- A compatible MCP client that accepts a remote Streamable HTTP endpoint and an Authorization bearer
  header.

Some MCP clients currently require an OAuth login and do not accept a manually configured bearer
token. Those clients cannot yet connect directly to Reality using this flow.

## 1. Find the endpoint

Open **Company settings → Agents → MCP Server** and copy the displayed endpoint. Deployments publish
this value as `MCP_URL`. Production endpoints use HTTPS and the origin root, for example:

```text
https://mcp.example.com/
```

Do not append `/mcp` unless the displayed deployment URL includes it. The displayed URL is the
authority.

## 2. Create a restricted token

Create a named token for one client, for example `Warehouse analyst in Claude`. Select the smallest
tool allowlist that supports its job. A read-only analyst normally needs discovery and relevant read
tools, not every current and future tool.

Reality shows the clear token once. Copy it into the client immediately. Reality stores only its
hash and a short display prefix.

## 3. Configure the client

Client interfaces differ, but the connection contract is the same:

```text
Transport: Streamable HTTP
URL:       <the displayed MCP_URL>
Header:    Authorization: Bearer <the token shown once>
```

Use the client's secure credential storage. Do not put the token in a repository, prompt,
screenshot, shared document, or source payload. Product-specific menu names and configuration syntax
belong to the client and may change independently of Reality.

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
- **Client asks for OAuth**: the client may not support manually configured bearer authentication.
- **Empty result**: verify the business reference, tenant, source coverage, filters, and freshness.
- **Unknown execution result**: inspect the proposal execution status and do not retry blindly.

## Revoke access

Return to **Company settings → Agents → MCP Server** and revoke the named token when a client is no
longer used, a device is lost, or a credential may have leaked. Revocation blocks subsequent calls;
create a separate replacement token instead of sharing one token between clients.

## Current authentication boundary

Reality currently uses manually created, tenant-scoped bearer access tokens. It does not currently
provide an OAuth 2.1 authorization flow, PKCE, dynamic client registration, or refresh-token
rotation. Therefore connection is configured rather than one-click. Check the product's current
settings and documentation before assuming a client-specific login flow is available.

This also means Reality does not currently offer unattended company provisioning for an external
agent. Browser setup establishes the human identity, company membership, and deliberate grant of
access; the MCP token is the agent credential after that point.

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
