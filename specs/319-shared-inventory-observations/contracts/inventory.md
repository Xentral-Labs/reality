# Inventory Read Contract

Existing tool and HTTP schemas stay compatible. Inventory rows retain item, physical, reserved, blocked, available, incoming, projected, receipts and issues. Numeric values remain Decimal internally.

Web `inventory_page` retains its signature, pager, filters and sorting. It delegates business derivation to an application service. Company-wide projections consume the same shared inventory observations. A selected location changes contributing quantities, not the underlying rules.
