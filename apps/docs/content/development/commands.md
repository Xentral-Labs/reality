# Implement Business Operations

A command changes business state. Use the existing stock reservation as a complete example.

The generated [Tool Usage reference](../tool-usage/commands) shows what already exists, with the
exact public parameters of every agent tool.

## Follow `reserve` through the code

1. `packages/reality-core/src/reality/services/core.py::reserve` owns the rules. It loads the
   `Commitment` with tenant scope, checks holds and inventory identity, calculates quantities with
   `Decimal`, creates the `Reservation`, and emits the Business Event.
2. `packages/reality-core/src/reality/tools/application.py::_reserve` translates application
   arguments into that service call and returns stable IDs plus `requested`, `applied`, `shortage`
   and `event_id`.
3. The same file registers `TOOLS["reserve"]` with `mutating=True`. Proposal and approval handling
   therefore recognizes the operation as a mutation.
4. `packages/reality-core/config/command_catalog.yaml` describes reads, writes, effect, parameters
   and adapters. `workspace_catalog.yaml` places it as the `reserve_stock` action.
5. HTTP, MCP, CLI and Chat call this application capability; they do not implement reservation
   rules.

```python
def reserve(session, tenant_id, commitment_id, quantity=None, *, action_id=None):
    commitment = _tenant_record(session, Commitment, tenant_id, commitment_id)
    require_not_held(session, tenant_id, "commitment", commitment.id)
    # validate, calculate with Decimal, create Reservation, emit event
    return ReservationResult(...)
```

The wrapper returns an application result, not an ORM object:

```python
def _reserve(session, tenant_id, arguments):
    result = reserve(session, tenant_id, arguments["commitment_id"], arguments.get("quantity"))
    return {"reservation_id": result.reservation.id,
            "requested": result.requested, "applied": result.reserved,
            "shortage": result.shortage}
```

## Add a command step by step

1. Add a failing business test under `packages/reality-core/tests/`. State preconditions, records
   written, event emitted and authoritative verification read.
2. Implement the tenant-scoped service in `src/reality/services/`. Do not accept a document number
   or SKU where an opaque ID is required.
3. Add the wrapper and `Tool(...)` entry to `tools/application.py`. Mark every state-changing tool
   as mutating.
4. Add the command to `config/command_catalog.yaml`. If a human can trigger it, add an action to
   `config/workspace_catalog.yaml` with prerequisites, confirmation and result kind.
5. Add only the adapters needed. Agent mutations use `create_change_proposal`; the stored proposal
   contains the exact tool, arguments and server preview and runs only after separate approval.
6. Test the service, application tool, catalog and each adapter boundary.

Useful examples are `test_inventory_and_fulfillment.py`, `test_application_tools.py`,
`test_application_catalog.py` and `test_http_boundary.py`.

Do not use a command for a read-only calculation, a current risk condition or ERP transport. Those
belong to a Projection, Exception or connector respectively. Never add delivery or reservation
status to a Document; derive it from Reality records.
