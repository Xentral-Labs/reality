# Add Entrypoints

## Which surface does the existing capability need?

The business query or operation must exist first. An entrypoint makes it accessible without defining
another business rule. If the operation is missing, start with [Commands](/development/commands).

| Entrypoint | User                           | Template                                | Guide                                                                                                              |
| ---------- | ------------------------------ | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Agent Tool | Agent or Chat                  | `inventory_read`, `reservation_propose` | [Agent Tools](/development/agent-tools)                                                                            |
| Web Action | Human in a workspace           | `reserve_stock`                         | [Web Actions](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/development/web-actions.md) |
| HTTP API   | Supported client               | `tenant_inventory_control`              | [API and CLI](/development/api-cli)                                                                                |
| CLI        | Development and administration | `commitment_reserve`                    | [API and CLI](/development/api-cli)                                                                                |

For read presentation, use
[Views](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/development/views.md).
A View can reuse an existing read model without a new Projection.

## What entrypoints share

All use shared services or Application Tools. Each preserves tenant scope, typed inputs and safe
errors. A subsequent read verifies the authoritative result of a mutation.

Read Agent Tools can read immediately. Mutating Agent Tools create a `ChangeProposal` with an exact
server preview. Execution requires separate explicit approval; read permission is not mutation
approval. Web Actions use the existing confirmation surface. Their chapters provide the complete
templates.

## Where to start

Follow the [first extension](/development/first-extension) or open the relevant guide. The
[shared reference](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/development/reference.md)
covers repository locations, workflow and verification rules. The running API’s `/openapi.json`
describes HTTP; the MCP catalog describes Agent Tools and their inputs.

[API and agent interface overview](/api-tools/) explains access paths, authentication and the
running OpenAPI reference.
