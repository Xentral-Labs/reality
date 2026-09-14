# Contract: Auditable Ledger Reversal

## Snapshot

`GET /api/tenants/{tenant_id}/ledger/posting-groups/{posting_group_id}/reversal`

Returns canonical revision, group integrity, derived role/status, eligibility/guidance,
entries, current chain, affected allocations, before-values, and Evidence availability.
Reading either role resolves the same chain without foreign disclosure.

## Preview

`POST /api/tenants/{tenant_id}/ledger/posting-groups/{posting_group_id}/reversal/preview`

```json
{
  "expected_revision": "sha256-hex",
  "reason": "Payment was posted to the wrong party",
  "actor_context": {"surface": "web"}
}
```

Returns normalized original entries, exact inverse entries, affected allocations,
before/after account, open-item, and payment values, revision, and canonical request
fingerprint. Preview performs no writes and uses shared application behavior.

## Execute

`POST /api/tenants/{tenant_id}/ledger/posting-groups/{posting_group_id}/reversal`

Accepts the previewed request plus its fingerprint. Execution locks and revalidates the
complete group, revision, fingerprint, and settlement state. Success returns reversal
ID, original/reversing group IDs, normalized effects, affected allocation IDs,
`replayed`, reversal time, and Inspector link.

Identical retry returns the existing result with `replayed: true` and no new entry,
relation, allocation, or event. Divergent, concurrent-loser, or stale execution conflicts
with refresh guidance.

## CLI

`reality ledger reverse POSTING_GROUP_ID --reason TEXT`

Print the shared preview and require confirmation. Abort has no effect. `--yes` is
explicit non-interactive confirmation and still prints preview and final opaque IDs.

## Agent and MCP

`ledger_reverse` is a mutating application tool with the same semantic arguments. Chat
and MCP create a durable ChangeProposal from the shared preview; only the existing
separate approval execution operation may reverse the group.

## Read surfaces and event

Journal/posting-group rows expose `normal`, `reversed_original`, or `reversing` role.
Allocation rows expose derived active/inactive state. Inspector traversal from either
group exposes both entry sets, reason, actor/time, original Evidence/Source, allocation
effects, net values, and relevant events.

One successful non-replayed operation creates `ledger.reversed` after inverse entries
and LedgerReversal are persisted but within the same transaction before commit. It is
subject to the original group; payload includes reversal and both group IDs, reason,
optional actor context, affected allocation IDs, and before/after effects. It invalidates
all affected financial register, exception, timeline, and projection consumers.

## Failures

- Missing/foreign group or references: non-disclosing not found.
- Blank reason, invalid/incomplete/unbalanced group, or reversing-role target: validation
  error with no effect.
- Stale preview, divergent existing relation, or race: conflict with refresh guidance.
- Relation, entry, event, or projection persistence failure: full rollback.
