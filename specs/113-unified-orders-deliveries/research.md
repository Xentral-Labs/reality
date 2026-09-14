# Research

Research delegated to finance_read_audit under speckit-plan and reviewed by the implementer.

Decision: extend canonical delivery_work instead of migrating commitment-control output. Rationale: commitment-control currently serializes original due/quantity despite effective filters, lacks unit and can label supplier rows with the receiving company. delivery_reads already provides effective values and correction-adjusted quantities, shared with customer actions. Preserve customer case boundary and extend only register direction/order criteria. Alternative of fixing all legacy commitment-control semantics would broaden this increment unnecessarily.

Decision: explicit customer/supplier order-document tabs using the existing evidence API. It supports a single exact type and filters before pagination; do not merge sales/purchase pages in JavaScript. Documents remain received evidence; no order-level readiness badge, projection or financial total is invented.

Decision: customer Open delivery reuses Your work, incoming Explain uses commitment Inspector. Supplier receipt execution remains a later scoped action. No browser calculation or direct ORM write. Exact order association follows DocumentLine when present, then direct Document FK. IDs and names are never interchangeable.

All unknowns resolved; no new external library or changing external technical fact required research.
