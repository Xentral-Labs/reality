# Data Model: Auditable Ledger Reversals

## Persistence decision

Add one tenant-scoped `LedgerReversal` table as direct durable correction Evidence.
Existing LedgerEntry and
SettlementAllocation rows remain unchanged and immutable. No historical backfill is
needed; absence from the relation means a normal group and active allocation.

## LedgerReversal

| Field | Meaning and constraint |
|---|---|
| `id` | Server-generated opaque primary identity. |
| `tenant_id` | Required tenant owner; indexed and enforced by every query. |
| `original_posting_group_id` | Required existing opaque group identity; unique. |
| `reversing_posting_group_id` | Required new inverse group identity; unique. |
| `reason` | Required trimmed durable business reason. |
| `reversed_at` | Required UTC acceptance time. |
| `actor_context` | Optional bounded canonical serialized authenticated/action context. |
| `request_fingerprint` | Required canonical semantic fingerprint; tenant-unique. |

A database check requires distinct role IDs and per-column uniqueness prevents reuse
within one role. Posting groups are existing logical
aggregates represented by the same opaque identifier on several LedgerEntries; because
that value is intentionally not unique on LedgerEntry, the service locks every original
group entry and proves cross-role absence, group existence/completeness, and tenant
ownership. Concurrency proof is required for this combined boundary.

## Entry roles and inverse rules

- **Normal**: Its group is absent from the relation.
- **Reversed original**: Its group appears as `original_posting_group_id`; entries remain
  immutable and retain direct business Evidence provenance.
- **Reversing**: Its group appears as `reversing_posting_group_id`; contains exactly one
  inverse per original, preserves account/party/amount/currency, swaps side, and carries
  no copied Document/SourceRecord; LedgerReversal is their direct correction Evidence.

Both groups must be balanced, single-currency, and party-consistent. A group may appear
in only one role and reversing groups cannot start another relation.

## SettlementAllocation derived state

An allocation remains stored unchanged. Its derived `active` value is true only when:

1. its payment and invoice entries belong to the same tenant as the allocation; and
2. neither linked entry's posting group is a reversed original.

Inactive allocations contribute zero to invoice settled amount and payment allocated
amount. The unaffected side is thereby reopened/released without rewriting history.
Views expose inactivity and the related reversal identity/reason.

## Revision and retry

The snapshot revision canonically covers original group entries, any reversal relation,
and allocations touching any original entry. The request fingerprint covers tenant,
original group, and trimmed reason. Actor context is excluded from semantic identity.

```text
eligible + preview → no persistent change
eligible + unchanged confirmed preview → inverse group + relation + one event
same request → existing result, replayed
different request / stale state / concurrent loser → conflict, no effect
group already in reversing role → invalid, no effect
```

## Migration and rollback

Migration `0029_ledger_reversals` creates the table, uniqueness/check constraints, and
indexes. Upgrade precedes application code. Empty-table downgrade is supported; once a
row exists, downgrade refuses because removing the relation would corrupt allocation
and correction interpretation. Code rollback retains the additive table.
