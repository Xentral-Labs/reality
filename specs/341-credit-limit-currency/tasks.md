# Tasks: Credit Limit and Orders in Another Currency

- [x] T001 Tests: a USD order against a EUR limit is held with the reason, with an EUR order within the limit as control; no limit holds nothing in either currency; an owner releases it and a raise asks again; an assigned line carries the order's reason.
- [x] T002 `credit_exposure.hold_if_over_credit_limit` holds an order in another currency; shared `_place_holds`.
- [x] T003 `order_line_items._hold_like_its_order` copies the order's hold reason.
- [x] T004 Spec 298 edge case, journey C07, coverage, coverage matrix.
- [x] T005 Credit, journey, advisor and catalog tests; `make docs-generate`.
