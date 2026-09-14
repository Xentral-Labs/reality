# Contract: Specialized Workspace Views

## Application reference

`GET /api/tenants/{tenant_id}/application-reference` adds these validated definitions:

- Order Operations: Orders (`fulfillment_queue`), Fulfillment blockers (`fulfillment_blockers`), Supply & demand (`item_supply_demand`).
- Warehouse Operations: Warehouse Queue (`fulfillment_queue`), Fulfillment blockers (`fulfillment_blockers`), Supply & demand (`item_supply_demand`).

The same materialization may support two View definitions. `tenant_usage` and `price_resolution` remain absent.

## Bounded read

`GET /api/tenants/{tenant_id}/projection-views/{projection_name}` accepts `page` (default 1), `size` (default 50, maximum 100), and optional case-insensitive `query`.

```json
{"items": [], "page": {"number": 1, "size": 50, "total": 0, "pages": 0, "has_previous": false, "has_next": false}}
```

Only the three in-scope projections are accepted. Unknown and excluded names return 404. Existing authentication, membership, and cross-tenant behavior applies.

## Product Web

- The sidebar renders `workspace.views.slice(0, 4)`.
- `More views` contains the complete ordered set.
- Search matches localized labels and descriptions case-insensitively.
- Selection closes launcher and mobile navigation.
- Specialized routes use explicit business columns, not arbitrary raw JSON.
