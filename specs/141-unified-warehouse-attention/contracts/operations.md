# Read contracts

Tenant prefix `/api/tenants/{tenant_id}`; existing auth plus ordinary-company guard.

- `GET /warehouse/{view}`: view is stock/reservations/movements; query `q`, `state`, optional exact `item_id`, page >=1 and size 1..100. Stock states empty/available/fully_allocated/shortage; reservation states empty/active/released/consumed; movement states empty/receipt/shipment/transfer/correction/return/supplier_return/adjustment. Unknown state rejected. Returns items, page, scope, observed_at. Stock rows expose item identity/name/SKU/unit plus physical/reserved/available. Reservation rows expose record identity, quantity/state/time, item/location labels and exact commitment/optional customer-delivery target. Movement rows expose recorded type/quantity/time/item/from/to locations, correction role and commitment/optional customer-delivery target.
- `GET /attention`: query `q`, severity empty/critical/high/normal/low, page/size; returns canonical matching items, page and observed_at. Search covers canonical identity, class, title, impact and subject reference. Ordering remains canonical severity/class/time order.
- `GET /attention/{id}`: current canonical explanation, resolution guidance from the catalog and exact target. A resolved or foreign finding is 404. No side effects or stored dismissal.

Frontend `/app/warehouse` selection: warehouse_view, item, entry, q, state, page. `/app/attention`: exception, q, severity, page. All stay tenant-scoped and clear on company switch. Selecting stock → related rows uses item equality, never labels. Selected entry opens Inspector; finding detail can open its canonical subject or exact customer case.
