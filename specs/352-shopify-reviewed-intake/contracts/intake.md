# Interface contract: Reviewed Shopify orders, changes and refunds

**Status**: Proposed interface contract; not an available-runtime API claim.

## Operations and payloads

Shopify enqueue retains its raw-source contract. Processing returns prepared, needs_review, stale/conflict, or applied/replayed result plus exact source/proposal references. The synchronous ingest helper must not report an accepted order or commitments before approval. Review includes first-order mapping or later-version before/after facts and coded blocked effects. Approval uses intake.approve, never a Shopify-specific bypass. Each refund source is a separate reviewable business unit.

## Shared outcomes

Use explicit classifications: raw received, prepared/awaiting decision,
needs_review, stale/conflict, rejected, executed/applied, failed with known no
effect, or unresolved execution. An import queue completion is not proof of business
acceptance. Scoped reads return source/proposal/receipt references and safe reasons;
they do not expose artifact storage paths or credentials.

## Authorization and replay

Tenant and actor come from the server-owned context. Recheck current relevant
authority at confirmation/application. Exact content digests and opaque IDs bind
the offered review; renewing a review invalidates the old digest. Replay returns
retained receipts. Unresolved execution requires reconciliation before redispatch.

## Adapter obligations

Web, CLI and MCP call shared services and retain their existing stronger permission
checks. No transport implements matching, stock correction or posting logic. Every
important displayed effect links to source and decision; all recovery/status reads
are side-effect free. Unknown/legacy attribution is shown truthfully.
