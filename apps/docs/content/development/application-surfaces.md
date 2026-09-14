# Expose Functions through API and MCP

The generated [Tool Usage reference](../tool-usage/commands) lists access class, parameters,
required fields and defaults for every currently registered tool.

Domain and application services own behaviour. Web, API, MCP, CLI and Chat are adapters to that same
capability.

## Choose the surfaces

- Add a Web View when a human role repeatedly needs the result in daily work.
- Add an API operation when another supported client needs the application contract.
- Add an MCP tool when an enterprise agent must discover and invoke the capability.
- Add CLI exposure for development or operational administration.
- Let Ask Reality use the registered application tool; do not create a Chat-only business path.

Reads may execute immediately. Mutations initiated by Chat or an agent create a
`ChangeProposal(status=proposed)` with an exact server preview and require separate human approval.
Permission to read a record never implies permission to mutate it.

Every adapter preserves tenant scope, typed validation, safe errors and the same verification read.
The running API's `/openapi.json` is authoritative for HTTP. The MCP catalog is authoritative for
agent tools and their input schemas.

## Where to make each change

| Surface         | File                                                     | Responsibility                                   |
| --------------- | -------------------------------------------------------- | ------------------------------------------------ |
| Shared tool     | `packages/reality-core/src/reality/tools/application.py` | validate arguments, call service, shape result   |
| HTTP            | `packages/reality-core/src/reality/web/api.py`           | request/response model, auth and tenant boundary |
| HTTP read model | `packages/reality-core/src/reality/web/read_models.py`   | compose read output, never mutate                |
| MCP             | `packages/reality-core/src/reality/mcp/catalog.py`       | discoverable name, JSON schema and tool mapping  |
| Web client      | `apps/web/src/api.ts`                                    | typed HTTP call                                  |
| Web workflow    | `apps/web/src/App.tsx` and feature components            | presentation and user interaction                |

## Example: expose a mutation to an agent

First confirm that the service and application `Tool` already exist. Add an MCP proposal definition
whose input schema uses opaque IDs. Map it to the existing application tool, not to the ORM or
service internals. The call creates a `ChangeProposal`; a separate approval call receives
`proposal_id` and `approved`. After execution, read the authoritative register to verify the result.

For HTTP, define a Pydantic request/response model and route that calls the same service or
application tool with the authenticated `tenant_id`. Check the generated `/openapi.json`, then add
the typed client method. A React component may decide how to display `shortage`; it may not
calculate availability differently from the service.

## Tests before the page is done

- application-tool test: exact argument and result contract;
- HTTP boundary test: auth, tenant isolation, validation and safe error;
- MCP catalog test: schema and mapping, including proposal requirement for mutations;
- Web test: loading, empty, error and success states without copied business rules.
