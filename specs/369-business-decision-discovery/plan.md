# Implementation Plan: Executed Decisions by affected order
## Technical Context
Python 3.12, SQLAlchemy 2, PostgreSQL; existing shared application discovery and MCP read contracts. No dependencies or schema changes.
## Constitution Check
| Principle | Result | Proof |
|---|---|---|
| Source → Evidence → Reality | PASS | Follow retained exact effect events; preserve sources. |
| Reality authority / shortest links | PASS | Line commitment membership precedes document fallback; Reservation/Movement → Commitment. |
| Proven schema | PASS | Existing action/event relationships only; no migration. |
| Tenant and shared services | PASS | Every subquery scoped; SQL lives in services/core.py, not MCP. |
| Spec/test gates | PASS | Accepted scope, regression first, complete CI required. |
| Explainable product | PASS | Existing tools point to exact review/status reads; no Web rules. |
| Simplicity / storage discipline | PASS | SQL EXISTS avoids duplicate pages; transient metadata only. |
| Received values | PASS | No recomputed source values or stored derivations. |
Post-design check: all PASS; no exception.
## Design and Order
1. Add fail-first proofs to tests/test_business_decision_discovery.py and HTTP grant test to tests/test_mcp_http_runtime.py.
2. Extend services/core.py AGENT_DISCOVERY_MODELS with executed_decision mapped to ChangeProposal, payload-free fields. Restrict status executed. Optional document_id validates a sales/purchase order and selects exact retained event membership for document, lines, commitments, reservations and movements. Tenant-scoped EXISTS binds action_id, deduplicating effects. Line links take precedence over document fallback. No source/party/item or JSON inference.
3. services/read_contracts.py retains filters/cursors and adds narrow coverage metadata for executed_decision. Legacy record metadata also states event association coverage.
4. tools/application.py remains the same discovery adapter. mcp/catalog.py exposes the family and documents document_id. Existing permissions remain unchanged. Update durable and generated reference.
## Test Plan
Executed reservation and movement, several events, unrelated shared labels/items, null-event/no-effect/pending states, shortest-line precedence, tenant collisions, foreign references, exact identity, pages/legacy, cursor refusal, payload privacy, exact review/status follow-up, read-only writes, HTTP grants. Relevant read/security regression suites, Ruff, docs/spec gates and complete CI. Fresh actual MCP reads against paused synthetic company, then external Claude discovery with no supplied Decision ID if available; no business replay.
## Migration and Rollback
No schema, fixtures, scheduling or operational rules changed. Revert additive family/guidance; existing grants and reads retain semantics. Temporary live tokens/containers are removed and revoked after testing; regular data volumes preserved.
## Risks and Review
Historic actions without retained exact execution events are intentionally undiscoverable by this filter. Coverage names this limit. No private payload is returned, nor is discovery a new approval permission. Live pagination is not a historical snapshot. No timing, shared-label or receipt-string association.
