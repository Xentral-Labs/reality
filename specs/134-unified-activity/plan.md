# Plan: Unified activity drawer
## Technical Context
React 19 / TypeScript / Tailwind, existing api.timeline and Inspector. No dependencies, schema, business rules or server changes.
## Constitution Check
| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | Existing event Inspector follows stored subject/source links | PASS |
| Reality owns state | Read existing events, no document status or derived success | PASS |
| Proven schema | No migration | PASS |
| Tenant and shared services | Existing tenant-scoped timeline/Inspector only | PASS |
| Spec and test evidence | FR-001..006 map to browser proof and existing service tests | PASS |
| Explainable web | Human labels with exact event/payload evidence | PASS |
| Storage discipline | No persistence, dependency or mutation | PASS |
| Received values | Original business values preserved | PASS |
## Design and Implementation Order
Domain, services and tools remain unchanged because all required behavior already exists. Adapter implementation is apps/web/src/unified/ActivityDrawer.tsx plus Shell.tsx header integration. Native dialog owns focus, dismissal and scrolling; Inspector opens a nested dialog. State is discarded on close/company change. A request generation counter rejects stale reads and cleanup invalidates pending responses. Filters trigger first-page reads; explicit older reads append unique IDs and retain rows on failure. Cursor comes from raw last returned event, never from deduplicated rows. No grouping, summary counts, polling or area filters.

Known event types use localized UI titles. Structured business context prints original party/item/reference/name/SKU/quantity/amount/currency/unit, using labels only where useful. Backend fallback remains available for unknown events. Show recorded timestamp; event time in details and explicit window semantics. Safe subject families only. Technical fields and JSON are React-escaped.
## Tests Before Implementation
apps/web/scripts/unified-activity-browser.mjs intercepts all API traffic and fails unexpected writes. Observe missing Activity header first. Cover page/cursor/failure/race/filter behavior, selected company, nested Inspector, focus, unchanged workspace input, context and technical payload, empty/read-error/retry, and 16 localized theme/viewport screenshots. Run existing unified browser regression, all contracts, i18n tests/audit, build/format, full PostgreSQL suite, lint/spec/diff checks.
## Rollback and Risks
Remove the header entry and component to roll back; no migration. Legacy history remains available until cutover acceptance. Historical classification and occurrence-versus-recording time are explicitly explained. Unknown event titles can remain server language; no invented translations of business values. No constitutional exceptions.
