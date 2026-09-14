# Plan: Customer refunds from open credits
## Technical context
Existing Python 3.12, SQLAlchemy/PostgreSQL and React/TypeScript. Reuse customer_refund_post application tool, canonical refund postings/allocation and the payment review/proof engine with an explicit customer_refund variant. No dependencies or schema changes.
## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Provenance | Existing refund document/events and optional source; exact attributable ledger/allocation proof | PASS |
| Reality | Open credit derived from active ledger/allocations; stock untouched | PASS |
| Schema | Existing documents, ledger and settlement links suffice | PASS |
| Tenant/services | Shared preview and canonical service, tenant queries and early shared lock | PASS |
| Test-first | Partial, netting, stale, precision, rollback, recovery and concurrency proofs first | PASS |
| Explainability | Credit/refund/ledger/source links in shared card | PASS |
| Simplicity | Parameterize existing payment proof; separate refund labels/form | PASS |
| Received values | Exact stated amount, no rounding or bank execution | PASS |
## Design
core.py adds private refund preview using the existing payment preview with explicit credit target and outgoing cash variant. Canonical post_customer_refund revalidates under the tenant lock before recording. Keep optional source/reference/effective time, standalone record_customer_refund and Playground finance intent unchanged.
services/payment_actions.py includes customer_refund_post, normalizes internal creation descriptors for shared proof, snapshots allocations on both control endpoints, checks exact refund document/events/postings/allocation. Historical evidence remains independent of current reversal state. No new event family. delivery_actions.py reuses payment routing and passes actual tool to overlap guard. financial_reversal_actions.py includes refund credit control and same-credit unresolved overlap. business_locks.py includes refund entry before reads.
web/api.py permits refund preparation. RefundCard.tsx uses the common proposal lifecycle with a credit-note selector, optional reference/time, explicit remaining-credit review and correct outgoing-cash wording. Finance row seeds credit opaque ID; Actions/Chat/Decisions share the card. api.ts adds refund types/wrapper. Existing documents selector can list credit notes; service rejects non-open selection, UI explains its outcome. Prefer an existing open-items credit filter if available after read audit.
## Risks and rollback
Credit netting uses the opposite allocation endpoint, so both endpoints must bind review. Ledger reversal overlap includes allocation counterparts. Exact proof must verify actual refund document alongside emitted snapshots. Roll back entry wiring while preserving historical records and old service signatures. No migration.
## Verification
New tests/test_unified_customer_refund.py covers all FR/DR, isolated PostgreSQL competing connections, HTTP authorization/prepare, rollback and proof corruption. Browser script covers selected Finance credit, launcher, Chat/Decisions, edit/reject, lost response and four languages at 390/1440 light/dark. Run adjacent payment/credit/reversal browser tests, complete backend, root lint/spec/diff, frontend build/contracts/i18n/format. Shared runtime login/form reads only.

Credit register refinement: existing invoice open-item projections exclude credits. Add explicit flow=customer-credit to the existing open-items endpoint, backed by private tenant-scoped _customer_credit_items with derived balances, status/search/sorting and 25/50/100 paging and separate currency totals. Existing invoice projection behavior remains unchanged. Finance exposes this flow and selected-credit actions; RefundCard requests only outstanding credits. No stored credit projection or schema. Add read/HTTP tests for filters, totals and pagination.

Test-first capacity finding: allocate_settlement counted the payer control only on its payment endpoint, allowing a refunded credit to be netted again. Regression observed failing; count both endpoints for payer capacity as already required by open_invoice_amount. This shared guard is necessary for FR-004 and covers refund versus netting in either order. No new authority or schema.
