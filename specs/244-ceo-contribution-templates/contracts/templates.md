# Contract: Contribution Template Catalog

The existing `graph.templates` read and Analytics HTTP route expose four entries:

- `contribution_overview`
- `contribution_by_month`
- `contribution_by_sales_channel`
- `contribution_margin_leakage`

Each retains the existing `key`, localized `label`, localized `about`, `question`, and optional `period` shape. Its published question starts at `contribution_valuation` and contains no cost-context identifier.

The client may adopt the question but must not call `graph.ask` until an explicit contribution context has been selected. Direct execution without context remains refused.
