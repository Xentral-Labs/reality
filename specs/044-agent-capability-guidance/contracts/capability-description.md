# Contract: Capability description

Stable application and MCP/Chat tool name: `capability_describe`.

## Input

```json
{"tool_name": "reservation_propose"}
```

Only an advertised agent proposal-tool name is accepted. Service names, internal
handlers, excluded operations, and administrative operations are not lookup keys.

## Result

```json
{
  "tool_name": "reservation_propose",
  "command": "Create reservation",
  "purpose": "Allocate available stock to an existing outgoing commitment.",
  "use_when": ["An outgoing commitment needs stock allocation."],
  "do_not_use_when": ["Goods have already physically moved."],
  "required_context": ["commitment", "item", "location"],
  "preconditions": ["The commitment belongs to the selected tenant."],
  "confirmation": "required",
  "idempotency": {"mode": "unsafe_retry", "guidance": "Reconcile unknown outcomes before retry."},
  "refusals": [{"code": "insufficient_stock", "description": "Requested stock is unavailable."}],
  "events": ["reservation.created"],
  "verification_reads": [{"name": "inventory", "kind": "projection", "proves": "Allocation reduces availability."}],
  "examples": {
    "use": [{"scenario": "Allocate stock for an existing commitment.", "reason": "Allocation is requested."}],
    "do_not_use": [{"scenario": "Record a completed shipment.", "reason": "This requires a Movement."}]
  }
}
```

## Failure and safety

- Unknown, internal, excluded, blocked, or ambiguous names return a bounded error.
- Lookup creates no proposal, action, Business Event, or Reality row.
- The description grants no authority and cannot execute a command.
- Existing proposal tools remain the only agent mutation entrypoints.

