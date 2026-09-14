# Implementation Plan: Unified Orders and Deliveries

## Design
Domain unchanged → extend canonical `packages/reality-core/src/reality/services/delivery_reads.py` → expose additive params in `web/api.py` → typed register client in `apps/web/src/api.ts` → `unified/OrdersPage.tsx`, routing/Shell/UnifiedApp/CaseAssistant. Reuse evidence document API, Inspector and customer `/app/work` case. No supplier mutation or new proposal type.

Extend `_query` with customer/supplier direction (default customer); select the supplier from from_party_id and customer from to_party_id. `_row` exposes type and correct party_id. delivery_work validates type and open/all, applies document criterion using coalesce of the tenant-scoped document-line document ID and direct commitment document ID before count/page. Existing effective_value and fulfillment_expressions provide revisions/corrections. delivery_case calls unchanged customer default, preventing receipt commitments from entering customer actions. Existing list client defaults remain unchanged; new register client passes typed options.

Three URL sections: deliveries, customer-orders, supplier-orders. Deliveries default customer/open; all history explicitly includes closed and cancelled rows. Document tabs have fixed sales_order/purchase_order filters, no merging paginated lists. Open a document Inspector or View deliveries with its opaque ID and matching direction/status all. Display a removable exact-order scope marker. Records are investigated through existing Inspector; customer Open delivery navigates to Your work. Advanced operations link to legacy orders. Registers have their own horizontal scroll container.

## Constitution Check
| Principle | Result | Evidence |
| --- | --- | --- |
| Source → Evidence → Reality | PASS | Documents and commitments stay distinct; exact links and Inspector. |
| Reality authority / shortest links | PASS | Existing effective quantity/fulfillment services; line link before direct document. |
| Proven schema | PASS | No schema, persistence or dependency change. |
| Tenant and services | PASS | All added SQL is tenant-scoped; no browser calculations or writes. |
| Tests first | PASS | New service/API and route/browser failures precede implementation. |
| English artifacts | PASS | Four UI languages, English code/docs/specs. |

## Tests and review
First add `tests/test_unified_orders_api.py` for incoming supplier/current values/unit, corrected receipts, open/all, exact line/document matching, foreign isolation and order types before paging; add route and `unified-orders-browser.mjs` tests. Preserve existing customer service/Inspector/action tests. Run full PostgreSQL suite, web contracts/i18n/format/build, all eight unified browser scripts, docs tests/format/build, spec policy/lint/diff checks and authenticated local preview. Inspect light desktop and dark mobile screenshots.

## Rollback
Remove the new unified route/sidebar entry. Additive API params keep existing defaults; no data migration or rollback. Legacy orders remains reachable, rollout/retirement separate.
