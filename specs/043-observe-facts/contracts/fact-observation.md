# Contract: Fact Observation

## Application operation

Stable tool name: `fact_observe`

Input:

```json
{
  "source_record_id": "src_opaque",
  "subject_type": "commitment",
  "subject_id": "cmt_opaque",
  "predicate": "order.shipping_priority",
  "value": "express",
  "observed_at": "2026-09-02T14:06:00Z",
  "idempotency_key": "caller-stable-key"
}
```

Output on first execution or identical retry:

```json
{
  "fact_id": "fct_opaque",
  "event_type": "fact.observed"
}
```

The operation rejects absent or foreign sources, absent or foreign subjects, unknown predicates, incompatible subject types, invalid values, empty idempotency keys, and conflicting reuse. No Fact or successful event persists on rejection.

## Agent proposal

Stable MCP/Chat tool name: `fact_observe_propose`. It accepts the same fields and produces a normal confirmation-required ChangeProposal. Only `proposal_approve_and_execute` may cross the mutation boundary.

## Predicate contract

```yaml
predicate: order.shipping_priority
subject_types: [commitment]
value_type: enum
allowed_values: [standard, express]
```

Unknown properties are rejected by the MCP input schema. Catalog validation fails startup/tests when predicate entries are duplicated or malformed.
