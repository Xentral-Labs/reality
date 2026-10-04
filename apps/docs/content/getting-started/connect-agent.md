# Connect your agent

Connect your agent to the company selected for your [starting recipe](./). Reality provides the same
business tools to external agents that its own app uses.

**Before you start:** Complete account signup, email confirmation and company setup in the browser.
Keep the intended company selected. This guide works for demo, new and existing-company pilots.

## 1. Copy the connection address

In Reality, open **Company settings → Agents → MCP Server** and copy the displayed endpoint. Use
that exact address; it belongs to the Reality installation you are using.

## 2. Connect and approve access

In your agent's MCP connection settings, add that address and start its sign-in flow. In the Reality
browser screen, sign in, select your ready company and approve the tools needed for reading orders,
inventory and their explanations.

Your client must support **Streamable HTTP and OAuth with PKCE**. The names and availability of its
connection controls depend on the client. Use the [MCP connection guide](/api-tools/connect-mcp) for
the complete connection contract and troubleshooting.

Start with read access. You can deliberately grant proposal tools later when you are ready for your
[first action](./first-action). An agent connection is scoped to the company you authorized; naming
another company in a prompt does not switch its access.

## 3. Check the connection

Copy this read-only prompt into the connected agent:

```text
Check which Reality company this connection authorizes. Show its identity and the
read capabilities available for our starting task. Do not change any data or switch
company. Explain any missing permission or setup instead of guessing.
```

**You should see:** The authorized company and the tools available to inspect its records. Compare
that company with the one you selected in Reality. An empty new company can still have a working
agent connection; it does not need a demo order.

For the demo recipe, also ask the agent to find **SO-006**. In the unchanged baseline, three of five
units are shipped and two remain open. Ask for the current records and their references.

If access is refused, check the connection and selected tool permissions using the
[connection guide](/api-tools/connect-mcp).

**Return to your recipe:** [Demo](./demo-company) · [From scratch](./start-business) ·
[Existing company](./existing-business).

## Prefer to stay in Reality?

Use the built-in **Chat** if AI is configured for your company. It uses the same application tools;
you can continue your recipe without setting up an external connection.

## MCP verification reads

For this recipe, deliberately authorize `company_context`, `capability_catalog`, `proposal_review`,
`proposals_awaiting_approval` and `proposal_execution_status` as reads, alongside the business reads
you need. Existing connections keep their allowlist; if a new read is refused, its absence from the
grant is not proof that the tool is missing. Proposal and confirmation tools require separate
deliberate permissions.

Use `company_context` for the stored company ID, name and purpose, then `capability_catalog` for
actual tool permissions. Use `proposal_review` for an exact decision preview and
`proposal_execution_status` for the execution receipt. Browser review links are optional; read
access never grants confirmation rights.
