# Plan: Invoice-linked customer credits
## Technical context
Existing Python/SQLAlchemy/PostgreSQL services, self-FK DocumentLine.billed_document_line_id, canonical sales_credit_record, credit postings and settlement allocation; React shared action cards. No schema/dependency/new public tool.
## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Provenance | Credit line→invoice line→order; immutable source retains reason and received amounts | PASS |
| Reality | Capacity/balances derived; no document operational state | PASS |
| Schema | Reuse existing typed self-FK with narrow target validation | PASS |
| Tenant/services | Core boundary delegates to private credit service; all queries tenant-scoped | PASS |
| Test-first | Capacity/atomicity/proof/stale/tenant/concurrency tests precede implementation | PASS |
| Explainability | Invoice/credit/ledger/source links and explicit balance impact | PASS |
| Simplicity | Existing command with distinct input shape; legacy return input untouched | PASS |
| Received values | No computed invoice amounts; allocation explicitly supplied | PASS |
## Design
services/credit_actions.py owns private invoice-credit context, preview, recording, review and proof helpers. Derive credits via typed invoice-line FK. Fully reversed credits release quantity/amount; unposted credits consume. Legacy order-linked credits block the affected invoice rather than guessing invoice attribution. Invoice must be posted with no reversed attached group. Quantity and header amount guards are independent of stated line/header reconciliation. Exact Decimal precision matches invoice entry.
core.py extends record_sales_credit with mutually exclusive invoice shape; preserves legacy positional signature. Credit lines may reference sales invoice lines; uncredited_return_quantity includes descendants. Existing canonical post_sales_credit_note and allocate_settlement perform Reality effects in one transaction. Emit attributable credit.recorded event with creation, exact receipt and snapshots. Historical proof validates source/document/lines/postings/allocation independently of current state.
delivery_actions.py routes only the invoice shape into shared review/recovery, retaining old Playground routing. Shared tenant lock covers canonical credit and posting/correction writers. Add unresolved invoice credit overlap and bind review to all credit/payment/reversal capacity state. web/api.py exposes read-only invoice credit context plus prepare allowlist. MCP schema extends existing proposal tool; no new command identity.
CreditCard.tsx uses existing modal/recovery pattern. Finance seeds invoice ID; Actions can select one. Chat/Decisions recognize shape. Show explicit allocation amount, no refund/stock effects, four languages. API types and Inspector links retain opaque IDs.
## Risks and rollback
Credit price-only adjustments represented as selected quantities cannot repeat indefinitely against a fully credited quantity; amount-only correction is out of scope. Legacy attribution ambiguity is blocked with explanation. Invoice/credit financial reversal affects capacity, not source history. Roll back new entry while retaining historical evidence/FKs. No migration.
## Verification
Isolated core tests for both partial/multi and paid/unpaid/no-return; two invoices/same order; legacy ambiguity; reversal/unposted credit; invalid/excess/precision; explicit netting; stale/concurrency/rollback/proof/recovery and HTTP tenant scope. Complete backend suite, Ruff/spec checks; frontend build/contracts/i18n/format; intercepted credit and adjacent invoice/payment/reversal browser journeys; shared login/form reads only.

Return exception readers include invoice-linked credit coverage for returned-not-credited, but financial credits without a return reference do not imply expected goods and must not create credited-not-returned exceptions. Update services/exceptions.py and the declared business event catalog; no new command identity.

Final review adds explicit referenced-position links in document and document-line Inspectors, tested through credit→invoice→order traversal. Tool/service descriptions cover both the new financial shape and legacy return shape.
