# Contract: Auditable Movement Correction

## Read correction snapshot

`GET /api/tenants/{tenant_id}/movements/{movement_id}/correction`

Returns the tenant-owned Movement, canonical revision, derived role/status,
`correctable`, safe eligibility/guidance, existing chain if any, normalized replacement
defaults, and direct SourceRecord availability. Reading from any chain member returns
the same chain without exposing foreign-tenant IDs.

## Preview

`POST /api/tenants/{tenant_id}/movements/{movement_id}/correction/preview`

```json
{
  "expected_revision": "sha256-hex",
  "reason": "Receipt quantity was keyed incorrectly",
  "replacement": {
    "type": "receipt",
    "item_id": "itm_opaque",
    "quantity": "7.0000",
    "from_location_id": null,
    "to_location_id": "loc_opaque",
    "commitment_id": "com_opaque",
    "source_record_id": null,
    "handling_unit_id": null,
    "lot_id": null,
    "serial_unit_id": null,
    "occurred_at": "2026-08-30T09:00:00Z"
  },
  "actor_context": {"surface": "web"}
}
```

`replacement: null` means void the original. Preview returns normalized original, exact
compensation, optional replacement, physical/fulfilment net effects, affected records,
canonical request fingerprint, and any blocking guidance. The fingerprint excludes
actor context because it identifies semantic correction intent, while actor context is
retained as audit metadata from the accepted execution. Preview performs no writes and
is calculated only by shared application behavior.

## Execute

`POST /api/tenants/{tenant_id}/movements/{movement_id}/correction`

Accepts the same semantic request plus the preview fingerprint. Execution revalidates
the revision, fingerprint, entities, and complete atomic outcome under the original
Movement lock. Success returns correction ID, original/compensation/replacement opaque
IDs, role/status, normalized net effects, `replayed`, corrected time, and Inspector link.

An identical successful retry returns the existing result with `replayed: true` and no
new Movement, relation, event, or derived effect. A different second request conflicts.

## CLI

`reality movement correct MOVEMENT_ID [replacement options] --reason TEXT`

The command prints the server-equivalent preview and asks for explicit confirmation.
Abort creates no effect. `--yes` is the explicit non-interactive confirmation and still
prints the preview and final opaque IDs.

## Agent/MCP tool

`movement_correct` is a mutating application tool with the same semantic arguments. Chat
and MCP create a durable ChangeProposal containing the previewed arguments. Only the
existing separate human approval/execute operation may invoke correction. The model has
no direct mutation path.

## Failures

- Unknown/foreign original or referenced entity: non-disclosing not-found behavior.
- Empty reason, invalid replacement, impossible inverse, compensation target, or source/
  tracking/hold violation: validation error with no effect.
- Stale preview, existing divergent correction, or concurrency race: conflict with
  refresh guidance and no effect.
- Event, relation, or persistence failure: full rollback.

## Read surfaces and event

Movement list/read models add derived role/status and chain IDs. Inspector traversal from
any member exposes reason, corrected time, actor context, net effect, each member's own
direct SourceRecord, and relevant events.

One successful non-replayed operation emits `movement.corrected`, subject to the original
Movement. Its payload contains correction, compensation, optional replacement IDs,
reason, actor context when supplied, and normalized net effects. It invalidates Inventory,
Operational Exceptions, Commitment register, Timeline, Fulfillment queue, Fulfillment
blockers, and Item supply and demand.
