# Plan: Multi-position invoices
## Technical context
Existing Python/SQLAlchemy PostgreSQL services, canonical application/MCP tools and React card. No new schema, dependency, tool or event vocabulary.
## Constitution Check
| Principle | Evidence | Result |
| --- | --- | --- |
| Source → Evidence → Reality | One manual source, invoice and N linked lines, balanced postings | PASS |
| Reality authority and shortest links | Existing billed_document_line_id, no document state | PASS |
| Proven schema | Existing many-lines relation suffices | PASS |
| Tenant and services | All validation/writes in core, canonical tools shared by adapters | PASS |
| Test evidence | Failing multi-position tests before core/UI implementation | PASS |
| Explainability | Every line and exact receipt available through shared review/Inspector | PASS |
| Simplicity | Extend existing invoice input and reuse lifecycle | PASS |
| Received values | Independent stated header and line amounts, no summation or rounding | PASS |
## Design
Extend core.py invoice entry with optional mutually exclusive lines input while preserving positional single-line calls and credit behavior. Pure preview validates each selected line plus same-order/distinct/storage constraints. Lock selected lines in sorted ID order before revalidation. Persist submitted order, independent amounts and full receipt atomically using existing document/posting services.
invoice_actions.py retains single-line review shape for legacy inputs, adds plural reference snapshots for batch inputs, intersects all selected IDs for unresolved work and verifies N+4 receipt records including all invoice lines.
mcp/catalog.py advertises both input shapes; tenant policy remains authoritative and existing practice input is not silently broadened.
InvoiceCard.tsx adds position rows, independent total, add/remove, plural review and backwards-compatible old proposal editing. api.ts exposes optional lines; localization.tsx supplies all four languages. Browser fixture covers both shapes and common entry/recovery.
## Validation / rollback
Full isolated core suite, focused multi/single/payment/credit tests, web contracts/build/i18n/format, invoice/payment/finance browser regressions and read-only shared preview. No source/test editing during full suite. Revert new entry availability without removing persisted source/events; old shapes remain readable.
