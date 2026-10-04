# Interface contract: Reviewed invoice, payment and allocation intake

**Status**: Proposed interface contract; not an available-runtime API claim.

## Operations and payloads

Financial prepare returns evidence, posting intent, optional exact allocation and coded issues. Required owner authority is the union of the proposed effects, evaluated by the central policy. A posting-only proposal is valid for unmatched payments; combined posting/allocation is one atomic approved unit. Currencies and monetary values use canonical decimal strings. Receipt links the source, proposal, document, posting identities and allocation if any; it never states that Reality transferred funds externally.

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
