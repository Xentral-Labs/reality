# Interface contract: Bulk intake settlement and delegated agent review

**Status**: Proposed interface contract; not an available-runtime API claim.

## Operations and payloads

Proposed bulk tools: intake.batch_prepare(exact_proposal_ids, request_id), intake.batch_review(batch_id, cursor), intake.batch_approve(batch_id, manifest_digest), intake.batch_status(batch_id, cursor), intake.batch_stop(batch_id). Review pages contain at most 100 member summaries; manifests at most 500 units; apply runs at most 25. Agent tools: intake.review_fetch(proposal_id, mandate_id, cursor) and intake.review_submit(proposal_id, digest, mandate_id, mandate_version, verdict, reasons, evidence_refs). Submission revalidates authority and exact review; a rejection/uncertainty is not an approval. Grant create/revoke are owner-governed proposals. The external agent must not be offered arbitrary mutation authority by these tools.

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

## Parent authorization and child decisions

Before confirmation the parent proposal is `proposed`. Exact bulk confirmation
persists a server-authored authorization and moves the parent to `executing`,
meaning a known authorized batch is queued/in progress, not an uncertain executed
business effect. The retained authorization binds parent ID, manifest revision and
digest, the exact child IDs/digests, reviewer identity/channel, decision timestamp,
authority basis and mandate ID/revision when delegated. Client fields cannot set
this identity. Membership and digests do not change after approval.

The queued worker does not become the reviewer. Before each child it resolves and
rechecks the original active person or token/mandate and the child's stronger
authority. Child attribution names that original reviewer; its receipt also cites
the exact parent authorization. Revoked membership, demoted owner, revoked token,
expired/revoked mandate or changed child/source/state yields a coded refusal for
that unit. No handler refreshes a child digest or grants itself fallback authority.
The parent's `executed` state is used only when all selected units have a retained
terminal batch disposition, including review-required/refused/stopped units; the
summary must distinguish partial/exception results from successful business apply.
Pending child decisions can be re-reviewed and placed in a new manifest explicitly.

The authorization section is immutable. Progress/control fields in the parent
batch output can change only through its locked shared service; they are not
independent approval or child receipts. Full child results derive from their
proposals/receipts plus explicit batch refusal dispositions.

## Durable queue shape and result bound

Scheduled continuation configuration contains only `{batch_id, manifest_revision,
continuation_id}`; it never includes 500 IDs/digests, raw source or complete
review. Resolve the frozen manifest from the tenant-scoped parent proposal.
Registry configuration stays under 15,000 bytes. JobResult stays within the existing
3,500-byte bound: counts, one parent reference and a continuation/result reference,
not child receipts. Full results are read via scoped pagination. A complete
500-order workload must exercise these exact serialized payload limits.

## Chunk transaction and stop semantics

Acquire the shared lock hierarchy and parent batch lock before a chunk starts.
An active chunk settles at most 25 units within the handler-owned transaction.
Each child's evidence/effects, attribution, outcome and receipt are inside its
savepoint. A known domain refusal rolls that savepoint back, then records a coded
no-effect disposition outside it. A database, connection, lease, timeout or unknown
failure aborts the whole chunk, including earlier provisional successes and
progress; it must not masquerade as an isolated business refusal.

Run success/progress and successful child receipts commit together. Retry after
chunk rollback can safely rerun its units; retry after commit replays receipts.
Stop takes the parent lock: it prevents the next chunk claim, while an already
running chunk may finish. Grant/revocation checks are current at the serialized
execution point; a revocation cannot cancel an already committed transaction.
Test middle-child domain refusal and later infrastructure failure separately.
