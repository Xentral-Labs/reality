# Research Decisions

- Existing paginators accept1–100; retain compatibility and expose25/50/100 in UI.
- Introduce db/query_order.py usable by services and web, not a web dependency in domain services.
- delivery_reads.delivery_work must sort effective_value/fulfillment_expressions, not stale original quantities/dates.
- read_models.inventory_page already has physical/reserved/available SQL expressions.
- reservation_page/movement_page/payment_page hydrate labels after paging; leave those labels unsortable. Their quantities, timestamps, status/type and currency use existing expressions.
- projection_page monetary JSON values require Numeric casts. Facts values remain heterogeneous original text, not guessed numeric types.
- source_metadata_page projects metadata only; sorting preserves payload exclusion.
- reference_workspace.reference_register has family-specific columns. Reset incompatible sort at variant changes.
- Retain semantic tables and explicit React row content; no grid dependency, client dataset sorting or unbounded fetching.
- Store only bounded UI preferences per signed-in user and table variant in localStorage. No cross-device requirement exists.
