# Contract: Workspace Application Reference

`GET /api/tenants/{tenant_id}/application-reference` retains its authenticated, membership-scoped behavior and adds `workspaces`.

```json
{
  "workspaces": [{
    "key": "warehouse",
    "label": "Warehouse Operations",
    "views": [{
      "key": "inventory",
      "label": "Inventory",
      "route": "inventory",
      "kind": "materialized_projection",
      "projection": "inventory",
      "description": "Inventory position and availability"
    }],
    "actions": [{
      "key": "record_movement",
      "label": "Record movement",
      "command": "record_movement",
      "target_route": "movements",
      "confirmation": "summary",
      "prerequisites": ["item", "location"],
      "result_kind": "movement"
    }]
  }]
}
```

Existing fields remain backward compatible. Arrays are deterministic and contain no tenant business values. References are validated before serving. A classified mutation must declare `Web` and a confirmation mode. Unknown references are deployment/test errors.

Workspace action order is the presentation authority. The sidebar shows at most the first two entries directly, while `More actions` exposes the complete ordered action array and never invents commands outside the validated workspace classification.

## Warehouse interaction contract

The client uses the existing explicit reservation, movement, movement-correction preview/confirm, commitment hold/release, handling-unit, lot, and serial-unit endpoints. No generic command execution endpoint is introduced.
