# Research

Read-only SpecKit research inspected canonical order creation, proposal lifecycle and
existing tests. No unresolved design question remains.

- Decision: extract pure document/order validation in core and reuse it for review
  and execution. Existing line normalization/pricing validation remain authoritative.
  Reject temporary writes or browser business rules.
- Decision: reuse common proposal endpoints and dispatch to order-specific review,
  proof and observation before delivery-only assumptions. Orders have no prior commitment.
- Decision: add the omitted stated header total to manual source payload. Never
  compute it. Preserve original richer supplied fields and normalized evidence separately.
- Decision: emit immutable order.recorded snapshot and exact IDs with action attribution;
  verify tenant-scoped linked records and creation events. Current line corrections or
  fulfillment cannot erase original proof. Do not require a newly created source event:
  an existing source without a document may still be used. An identical payload with
  an existing document is rejected before writes, respecting the unique source/type
  constraint. Distinct agreements may share a number and create distinct source versions.
- Decision: recheck relevant references and canonical validation under existing tenant
  lock; prevent another unknown identical-intent order without using human number as identity.
- Decision: reuse tenant-scoped suggestion search for company/party/item/location selectors;
  no invented active/role restrictions beyond canonical service semantics.

Regression review: manual line dictionaries also carry untyped source metadata such
as label. Preserve those fields losslessly; only top-level unsupported tool arguments
are rejected. Do not turn an adapter form's field list into a new domain restriction.
