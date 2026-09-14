# Contracts
- GET `/api/tenants/{tenant}/delivery-work`: existing q/page/size/status(open|all) plus commitment_type(customer_delivery default|supplier_delivery) and optional document_id. Validate direction/status. Return scoped page, current promised/fulfilled/open/reserved quantities, unit, correct counterparty and type. Existing customer-only case endpoint unchanged.
- GET `/api/tenants/{tenant}/evidence-documents`: reuse document_type sales_order or purchase_order; no API change.
- `/app/orders-deliveries?tenant=...&orders_view=deliveries|customer-orders|supplier-orders&delivery_type=customer_delivery|supplier_delivery&delivery_status=open|all&order=...&entry=...&q=...&page=...`.
- Customer case link `/app/work?tenant=...&commitment=...`; supplier row only shared commitment Inspector. No new write endpoint.
