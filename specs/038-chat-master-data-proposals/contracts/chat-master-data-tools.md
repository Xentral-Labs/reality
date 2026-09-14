# Contract: Chat Master Data Proposal Tools

## Shared proposal behavior

Each tool has `propose` access, accepts exactly one `records` array with at least one
same-family object, and returns:

```json
{
  "proposal_id": "act_opaque",
  "status": "proposed",
  "requires_human_confirmation": true,
  "arguments": {"records": []}
}
```

No business record is created until the existing separately permissioned confirmation
tool executes the proposal. Successful execution returns a `records` list containing
the family and created opaque ID for every input record in input order.

## `party_create_propose`

Each record requires `name` and `roles`. `roles` is a non-empty unique list limited to
`company`, `customer`, and `supplier`. Optional values mirror the existing Party create
contract, including `source_system`, `external_id`, and lossless `source_payload`.

## `item_create_propose`

Each record requires `sku` and `name`. `unit` defaults to `pcs`. Optional values mirror
the existing Item create contract, including optional source provenance.

## `location_create_propose`

Each record requires `name`. `type` defaults to `warehouse` and `allows_stock` defaults
to true. Optional values mirror the existing Location create contract, including parent
identity and optional source provenance. A record may declare a proposal-local `ref`;
later records use `parent_ref` to link to it. `parent_location_id` is accepted only for
an already-existing opaque Location identity. References resolve in input order.

## Failure contract

Unknown fields are rejected by the tool schema. Empty required strings, invalid domain
values, incomplete source identity, and foreign relationships are rejected by the
shared service. Confirmation failure preserves the pending proposal for inspection and
leaves all business/source state unchanged.
