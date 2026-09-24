# API & Tools

Reality exposes several adapters around the same application services. Choose the interface that
fits the actor, not a different business behavior.

| Interface          | Primary use                                    |
| ------------------ | ---------------------------------------------- |
| Product Web        | Authenticated human operation and inspection   |
| API                | Browser and integration HTTP boundary          |
| CLI                | Developer and operator workflows               |
| MCP                | Authenticated enterprise-agent tools           |
| Chat / Ask Reality | Conversational queries and confirmed proposals |

To use these capabilities from an external agent, follow [Connect an MCP client](./connect-mcp). The
guide covers the current HTTPS and OAuth setup, least-privilege permissions, a first read, governed
changes, verification, and revocation.

The current setup has one deliberate human step: a person signs in through the browser, selects or
creates the company, and approves a scoped OAuth grant. The agent works directly through MCP after
that handoff and must not automate the human signup or approval flow.

## Authentication and tenant context

Product Web uses a secure browser session. API calls validate membership before business access. MCP
uses its configured authenticated HTTP boundary. Every business request carries or resolves a tenant
context; cross-tenant reads behave as not found.

## Canonical OpenAPI

The running API exposes its canonical OpenAPI document at `/openapi.json` and an interactive
reference at `/docs`. Use the configured `API_URL` origin. Public Docs does not copy a second full
endpoint catalog because it would drift from the executable contract.

## Request shape

> **Example:** Tenant-scoped HTTP calls use supported resource paths and explicit request bodies.
> Consult the runtime OpenAPI schema for the exact method, path, payload, status codes, filters, and
> pagination of your deployed version.

## Errors, filters, and pagination

Treat authentication, authorization/not-found, validation, conflict, and server failures as
different outcomes. Never infer another tenant's existence from an error. Use only filters and
pagination described by the deployed OpenAPI contract; examples here are explanatory, not an
independent interface guarantee.

## Mutating agent actions

Read-only tool calls execute without confirmation. Mutations from Chat or an agent produce a
proposal/preview and require explicit confirmation. Confirmation invokes the same application
service that a human or CLI adapter would use.
