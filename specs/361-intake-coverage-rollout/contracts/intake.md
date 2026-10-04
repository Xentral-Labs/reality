# Interface contract: Intake decision coverage, demo and safe rollout

**Status**: Proposed interface contract; not an available-runtime API claim.

## Operations and payloads

Cutover sequence: add compatible schema; deploy preparation/apply services; stop/drain old writers; run idempotent pending-job transition; start only new workers; enable explicitly authorized reviewer clients. Source reads report prepared/awaiting decision separately from applied. Rollback disables review clients and drains execution while preserving raw capture and the admission guard. Existing historical detail reads retain unknown/legacy attribution. No deploy/merge is authorized solely by these design documents.

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

## Demo readiness

Distinguish source production running from interpretation waiting for review.
No mandate is granted by connect/start or previous source activation. Owner can
use human review or explicitly enroll a named external reviewer and issue its
bounded mandate. Missing, expired, revoked or unavailable reviewer leaves raw and
prepared work intact, shows awaiting-reviewer with actionable links and respects
existing saturation/pause/stop controls. Setup readiness must not pretend that a
live review client has been configured. Existing demos receive the same fallback
at cutover without reseeding or inventing past decisions.
