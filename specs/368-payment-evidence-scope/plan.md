# Implementation Plan: Payment evidence and selection scope
**Language**: English
## Technical Context
Python 3.12, SQLAlchemy 2/PostgreSQL, existing shared reads. No dependency or migration.
## Constitution Check
| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality, received values | PASS | Existing stated gross and qualified evidence only, no recomputation |
| Operational authority and shortest relationships | PASS | Canonical readiness unchanged; existing IDs only |
| Proven schema | PASS | Transient presentation, no stored field |
| Shared tools and tenant boundaries | PASS | Decorate existing scoped results, no new query |
| Spec and test evidence | PASS | Accepted scope, tests first and traced gates |
| Web explainability | PASS | Shared services, no browser rules |
| Simplicity, PostgreSQL and Decimal | PASS | Pure helper, existing arithmetic and storage preserved |
| English artifacts | PASS | Repository content English |
## Design
Add pure payment_interpretation to services/read_interpretation.py, consuming the already-computed readiness dictionary. Apply from canonical FulfillmentReadiness.as_dict and queue projection interpretation; include_interpretation=False remains unchanged for caches and shipment review. Metadata exposes amount_basis, payment_evidence and shipment_constraint plus a deterministic notice. Classify canonical codes, not duplicate qualification arithmetic; never infer actual zero payments from standard placeholders. Completed quantities mark constraint not applicable; releases do not rewrite amounts or blockers.
Add selection_record_count to read_contracts.discovery_summary: len(shown) only when no omitted keys in either direction, otherwise null. Explain record versus consignment units; never aggregate across cursor pages or query a separate count.
Update tool/native/demo guidance only where it explains these existing fields. No API input change.
## Research
Research-agent review confirmed standard placeholder ambiguity, order-scoped qualification, owner-release versus settlement, consolidated attribution and unchanged cache/token boundaries. See research.md.
## Test Plan
Use existing PostgreSQL business fixtures for standard, orphan, unstated, missing invoice, paid/unpaid, ambiguity, release and consolidated cases. Public dispatch proofs compare direct/explain/fresh/cached results. Assert metadata never enters cache or reviewed state. Discovery proofs cover partial first, final cursor, complete, empty and shipment filter. Retain authenticated HTTP, tenant/grant and existing business suites. Run focused tests, Ruff, spec/generated-doc gates, full CI and final review. External Claude acceptance uses a temporary same-company read-only credential, no proposal or execution.
## Migration and Rollback
None. Revert additive metadata and descriptions; no cache refresh or business repair required.
## Complexity Tracking
No exceptions. Post-design Constitution Check remains PASS.
