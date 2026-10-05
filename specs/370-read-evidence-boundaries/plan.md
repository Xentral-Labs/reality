# Implementation Plan: Evidence boundaries in existing reads

**Branch**: codex/read-evidence-boundaries | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)
## Summary
Reuse the existing coverage object in discovery_summary, qualify its first count sentence, add a transient order interpretation notice, and sharpen existing MCP descriptions. No operational calculation changes.
## Technical Context
Python 3.12+, SQLAlchemy 2/PostgreSQL, existing shared application read services, pytest and generated catalog. Same deployment and dependencies. Constant response guidance adds no queries; discovery pagination is unchanged.
## Constitution Check
| Principle | Pre-design | Post-design | Proof |
|---|---|---|---|
| Source → Evidence → Reality | PASS | PASS | Existing exact movement/source readers; no invented evidence |
| Operational authority | PASS | PASS | No document statuses or new business rules |
| Proven schema | PASS | PASS | Transient response guidance only; no persistence/schema |
| Tenant/service boundaries | PASS | PASS | Existing shared scoped reads; no adapter rules |
| Spec/tests before completion | PASS | PASS | Owner accepted scope, regressions before code, CI required |
| Explainable web | PASS | PASS | Shared response; no UI change |
| Simplicity/storage | PASS | PASS | No infrastructure/dependencies |
| Received values | PASS | PASS | Existing quantities unchanged; no recomputation |
## Project Structure and Implementation
- services/read_contracts.py: executed summaries copy existing coverage scope/completeness and start with qualified count. Ordinary families untouched.
- services/read_interpretation.py: static order_inventory_interpretation guidance.
- services/projections.py: order explanation includes that shared transient interpretation_scope. No extra histories are queried.
- mcp/catalog.py: discovery, order_explain and inventory_read descriptions preserve count scope and disallow hypotheses about uninspected inventory history. Existing movement_explanation is exact provenance, not complete history. Do not invent movement item/document filters.
- tests/test_read_evidence_boundaries.py: service/MCP/legacy tests; tests/test_mcp_http_runtime.py: authenticated response assertions in existing fixtures.
- docs/features/mcp_reads.md and generated catalog: contract update.
## Test Plan
Test scoped/unscoped/empty and first/intermediate/final pages, unaffected ordinary families and legacy, current stock with unrelated receipt absent from order-linked movements, completed/empty orders, exact callable provenance read, tenant isolation/read-only listener. Run relevant discovery/read/HTTP/interpretation regressions, Ruff/spec/docs gates and full CI. Fresh Claude test supplies no action ID; independently verify unchanged operational state, revoke temporary reads. Free-form answer success/failure recorded separately.
## Migration and Rollback
No migration. Revert additive guidance/summary fields; existing selections and values stay valid. Preserve regular stack/data volumes; remove isolated test runtimes and revoke temporary access.
## Risks and Review
Guidance reduces ambiguity but cannot enforce an external model's prose. Current stock does not prove absence of historical actions. Summary scope must derive from the existing coverage, not a second inference. No historical completeness claim on a final cursor page.
