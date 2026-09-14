# Data Model: Specialized Workspace Views

No persistence schema changes are introduced.

## Workspace View Definition

- `key`: unique stable product identity.
- `label`: canonical destination title.
- `route`: validated Product Web destination.
- `kind`: `materialized_projection` for specialized Views.
- `projection`: existing materialization from the Projection catalog.
- `description`: searchable business purpose.

One projection may support multiple View definitions, while each View key and route remains unique. Workspace membership is ordered and duplicate free.

## Specialized Projection Page

- `items`: bounded page of existing projection payloads.
- `page`: number, size, total rows, total pages, and previous/next flags using the existing pager contract.
- `projection`: `fulfillment_queue`, `fulfillment_blockers`, or `item_supply_demand`.

Rows remain disposable and tenant scoped. Existing opaque references preserve traceability; no new relationship is created.

## State Transitions

None. Opening, searching, and paging are read-only. Projection refresh remains owned by the existing service.
