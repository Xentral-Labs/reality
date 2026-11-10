# Audit findings

- prepare_graphql_order validates original selected GraphQL meaning then explicitly
  stops at the spec389 buyer mapping. It cannot currently prepare from that
  separately recognized relationship without a new reviewed mapping contract.
- prepare_order reads company/customer/location only from job.input. It builds a
  PreparedIntake with prospective document/commitment/credit-hold effects. Do not
  use it as a fake read-only diagnosis by rewriting or copying job.input.
- Item lookup selects the first same-tenant exact SKU without cardinality or active
  filtering. The preflight must expose ambiguity/inactivity, not inherit this as
  observed readiness. No change to the accepting preparation path in this slice.
- GraphQL projection preserves source total and unit prices but has no interpreted
  line amount, promised delivery or source sales unit. Unknown must describe
  selected/projection coverage, not missing facts in the entire upstream order.
- Item.unit is a stock master-data observation. It is not proof that the received
  Shopify quantity is in that unit; do not use implicit pcs or conversions.
- Existing canonical mapping reader independently verifies immutable historical
  approval and reports current source/customer flags, avoiding invented users or
  customer remapping. Existing tenant-scoped records and roles suffice for read
  diagnosis; no new table, authority or scheduler is needed.

- The existing accepted-order guard is now extracted without changing canonical
  preparation behavior. The same exact tenant-scoped query is shared by preflight,
  including a final optimistic recheck if acceptance changes during the read.
- Initial use of new services.intake._reference would not run on old schema99.
  The smallest compatible correction uses explicit stable observed-field hashes
  and a shared identity-read helper, not a copied intake subsystem or new models.
- Normal old MCP exposes complete catalogue metadata independently of a token's
  grants. Actual call admission, not tools/list presence, proves permission.
  HTTP proof checks unauthenticated401 and denial of ungranted generic approval.
