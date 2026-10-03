# Add Entrypoints

## Which surface does the existing capability need?

The business query or operation must exist first. An entrypoint makes it accessible without defining
another business rule. If the operation is missing, start with [Commands](./commands.md).

| Entrypoint | User                           | Template                                | Guide                        |
| ---------- | ------------------------------ | --------------------------------------- | ---------------------------- |
| Agent Tool | Agent or Chat                  | `inventory_read`, `reservation_propose` | [Agent Tools](./agent-tools.md) |
| Web Action | Human in a workspace           | `reserve_stock`                         | [Web Actions](./web-actions.md) |
| HTTP API   | Supported client               | `tenant_inventory_control`              | [API and CLI](./api-cli.md)     |
| CLI        | Development and administration | `commitment_reserve`                    | [API and CLI](./api-cli.md)     |

For read presentation, use [Views](./views.md). A View can reuse an existing read model without a new
Projection.

## What entrypoints share

All use shared services or Application Tools. Each preserves tenant scope, typed inputs and safe
errors. A subsequent read verifies the authoritative result of a mutation.

Read Agent Tools can read immediately. Mutating Agent Tools create a `ChangeProposal` with an exact
server preview. Execution requires separate explicit approval; read permission is not mutation
approval. Web Actions use the existing confirmation surface. Their chapters provide the complete
templates.

## Where to start

Follow the [first extension](./first-extension.md) or open the relevant guide. The
[shared reference](./reference.md) covers repository locations, workflow and verification rules. The
running API’s `/openapi.json` describes HTTP; the MCP catalog describes Agent Tools and their
inputs.
