# Contract: Reality Gap HTTP and MCP

## HTTP

- `GET/POST /api/tenants/{tenant_id}/reality-gaps` lists or captures.
- `GET /api/tenants/{tenant_id}/reality-gaps/{gap_id}` returns full detail.
- `POST .../{gap_id}/entries|recommend|decide|implementation|simulate|activate|disable|replay` performs the named shared operation.
- Classification and rule control are owner-only. Stale revisions conflict; foreign identities are not found.

## MCP and Chat

Read tools: `reality_gaps`, `reality_gap_get`, `reality_gap_questions`, `reality_gap_simulate`.

Proposal-only mutations: `reality_gap_create_propose`, `reality_gap_entry_add_propose`, `reality_gap_recommend_propose`, `reality_gap_decide_propose`, `reality_gap_implementation_prepare_propose`, `reality_gap_rule_activate_propose`, `reality_gap_rule_disable_propose`, `reality_gap_rule_replay_propose`.

Approval rechecks tenant, authority, and revision before exactly-once execution.

## Safe rule draft

```json
{"logical_name":"Shopify shipping priority","source_system":"shopify","source_type":"order","value_path":"note_attributes.0.value","predicate":"order.shipping_priority","subject_type":"commitment","subject_resolver":"source_document_commitments","value_type":"enum","allowed_values":["standard","express"],"normalization":["trim","lowercase"],"observed_at_mode":"source_received_at"}
```

Unknown properties and unsupported paths, resolvers, normalizers, or expressions are rejected.

Legacy `value_path` drafts are normalized to `output_mode: source_path` and `output_path: <value_path>`. New clients use the explicit form:

```json
{
  "logical_name": "High-value Shopify order review",
  "source_system": "shopify",
  "source_type": "order",
  "conditions_mode": "all",
  "conditions": [
    {"path": "total_price", "operator": "greater_or_equal", "operand": "1000"},
    {"path": "financial_status", "operator": "not_in", "operand": ["paid", "authorized"]}
  ],
  "output_mode": "constant",
  "constant_value": true,
  "predicate": "order.requires_manual_review",
  "subject_type": "commitment",
  "subject_resolver": "source_document_commitments",
  "value_type": "boolean",
  "observed_at_mode": "source_received_at"
}
```

Line rules additionally provide one `iteration_path`, use relative condition/output paths inside each element, and select `source_document_lines`. Simulation and replay responses expose `not_applicable`, invalid, ambiguous, conflict, created/existing Fact counts, representative outcomes, cumulative counts, and an opaque `next_cursor` when more sources remain.
