# Add Agent Tools

## What you will learn

Expose an existing operation to an agent and verify its read/proposal contract.

## When to use it

An Agent Tool is the callable interface for an agent. It is neither the business service nor a Web
Action. If the Command exists, add only the entrypoint. A read tool can read immediately; a mutation
tool prepares a proposal for separate confirmation.

## Before you start

The service and Application Tool already exist. For mutations, understand the exact preview and
separate approval path; for reads, use existing read permission. Start with the
[first extension](/development/first-extension) if needed.

## Worked example

Follow `reservation_propose` in `packages/reality-core/src/reality/mcp/catalog.py`. This is its
existing registry entry, used inside the existing module; `MCPToolDefinition`, `_object_schema`,
`STRING`, `OPTIONAL_STRING` and `_propose` are helpers in that module. The excerpt is not a
standalone Python file.

```python
MCPToolDefinition(
        "reservation_propose",
        "Propose reservation",
        "Prepare a stock reservation without allocating before confirmation. Without location_id it reserves at the promise's own warehouse; with it, the rest at that active warehouse holding stock (spec 303), for example one the stock_in_another_location finding names.",
        "propose",
        "Mutations",
        _object_schema(
            {
                "commitment_id": STRING,
                "quantity": OPTIONAL_STRING,
                "handling_unit_id": OPTIONAL_STRING,
                "lot_id": OPTIONAL_STRING,
                "serial_unit_id": OPTIONAL_STRING,
                "location_id": OPTIONAL_STRING,
            },
            required=("commitment_id",),
        ),
        _propose("reserve"),
    ),
```

The schema requires `commitment_id`; quantity and other dimensions are optional. Quantities travel
as exact decimal strings. `_propose("reserve")` maps the tool to the existing Application Tool.
Preparing the proposal does not allocate stock.

## Step by step

1. Specify and test inputs, result, read authorization and confirmation boundary first. Follow the
   repository's Spec Kit workflow.
2. Inspect the existing Command and `TOOLS` in `tools/application.py`; do not add a second service
   implementation.
3. Add a `MCPToolDefinition` with stable name, description and exact input schema. Copy only fields
   needed by your operation. Use opaque IDs and correct required fields.
4. Use the existing proposal path for mutations. Inspect the exact server preview; separate explicit
   human approval uses `proposal_approve_and_execute`. Follow its current approval/review contract
   rather than automatically setting `approved=True`.
5. For reads, follow `inventory_read` and `_read` in the same catalog. A query does not necessarily
   need a new Command or Projection.
6. Test discovery, schema, proposal without effect, rejection, approval, replay and tenant
   isolation. Templates under `packages/reality-core/tests/`: `test_mcp_read_contract.py`,
   `test_chat_mcp_business_commands.py`, `test_agent_command_parity.py`.
7. Give the tool a business-object home through normal catalog relationships. New
   Commands/Views/Projections need `resource_catalog.yaml` membership and German labels. Run
   `make docs-generate` and inspect the generated reference.

## Check the result

Use a test company with a real Commitment and stock. Resolve the opaque Commitment ID through
existing reads. Invoke the proposal tool with that ID and `quantity: "5"`: it returns a proposal
without creating a Reservation. Inspect the preview and explicitly approve that exact proposal. Read
Reservations and Commitments afterwards: applied quantity and any shortage must match the service
result. Another tenant must not be able to discover the record.

[Add Web Actions](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/development/web-actions.md)
explains the human entrypoint to the same operation.

## Try it yourself

Compare `inventory_read` with `reservation_propose`. Explain why one reads immediately and the other
returns a proposal. Change only a local training tool's description; its schema and business answer
must stay the same.

## Common mistakes

A schema alone does not make an operation safe. Do not write ORM rows, automatically approve
proposals or accept foreign identities. Do not expose a mutation as a read.

## Continue

[Web Actions](https://github.com/Xentral-Labs/reality/blob/main/docs/maintainer-guides/development/web-actions.md)
covers the human entrypoint; [API and CLI](/development/api-cli) covers additional adapters.
