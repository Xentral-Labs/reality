# Contract: Repeating Action Field

A repeating field declares a request key, business label, minimum rows, row defaults, and typed child controls. The renderer submits an array of objects under that request key. It never accepts or emits a JSON string for a typed list.

For `create_manual_order`, the field key is `lines`; required child keys are `item_id`, `quantity`, and `unit_price`. Optional child keys are `unit`, `description`, and `promised_at`.
