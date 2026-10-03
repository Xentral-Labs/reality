# Interface contract: Decision-gated interpretation and admission

**Status**: Proposed interface contract; not an available-runtime API claim.

## Operations and payloads

Proposed shared operations: intake.prepare(source_record_id, profile, mapping, request_id), intake.review(proposal_id), intake.approve(proposal_id, exact_review_digest), intake.reject(proposal_id), intake.result(proposal_id). Caller-supplied tenant/actor assertions are never authority. Preparation returns a pending proposal reference, source links, review digest, exact proposed fields/effects and coded issues. Approval returns a retained receipt only after atomic commit. Export package and manifest schemas for spec 355; manifest creation alone grants no execution authority.

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

## Processing phases and recovery

Each new terminal preparation/decision/application phase allocates one monotonic
outcome attempt under the ImportJob lock. Replay returns that phase's retained
result without another outcome or effect. A prepared result names a proposal;
only an applied result claims accepted evidence/Reality. Transient retry backoff
is phase-local and does not treat awaiting decision or rejection as failure.
