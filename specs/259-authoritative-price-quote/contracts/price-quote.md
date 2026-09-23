# MCP Contract: `price_quote_read`

Input requires `party_id`, `item_id`, positive decimal-string `quantity`, `direction` (`sales` or
`purchase`), ISO currency and unit. Optional `at` is an ISO UTC instant.

A match returns `matched: true`, normalized request context, the selected unit price, price-list and
entry opaque IDs, `source`, optional assignment/group opaque IDs, and `evaluated_at`.

No eligible tier returns the same normalized request context with `matched: false`. Invalid or
foreign IDs are refused through the canonical tenant-scoped lookup.
