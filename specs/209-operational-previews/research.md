# Research

- Decision: explicit preview sections, requested only by inline callers. Rationale: first-three-section truncation favors correction metadata. Alternative: reordering full Inspector sections would change all consumers.
- Decision: compose existing document_detail, delivery_case, stock_at/active_reserved, shipment_explain and bounded settlement reads. Rationale: no parallel business rules or schema. Alternative: browser calculations or full company register reads rejected.
- Decision: original description plus SKU; labeled current item-name fallback. Rationale: preserve historical evidence; current master data may have changed.
- Decision: named short links and bounded section rows; unknown remains unknown. No unresolved research questions.
