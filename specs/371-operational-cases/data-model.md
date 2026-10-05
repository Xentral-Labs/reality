# Approved first-slice coordination model

The owner approved the concrete five-table first slice on 2026-10-05; migration 0144 implements that slice. Broader examples below are not additional enabled tables.

## OperationalCase

Tenant-scoped opaque ID; kind; exactly one typed goal anchor; policy version; control mode; nullable takeover member; control revision; creation timestamp. Fulfillment anchor is Document, return anchor is ReturnAnnouncement; composite same-tenant FKs and a check enforce exactly the appropriate anchor. Unique tenant/kind/anchor yields one identity across replay/reactivation. A fulfillment case does not put operational state on Document; it groups existing customer-delivery commitments.

Refund anchor MUST reference an actual explicit intent entity, not an arbitrary string or refund evidence document. No refund schema column/intent entity is implemented until T002 proves an existing suitable authority or a separately reviewed intent design. Initial refund policy is capability-gated and successful refund evidence remains a reconciliation signal.

Control revision is needed for compare-and-swap and stale action refusal. Responsibility cannot be derived from movements, so it is stored. Goal completion, quantities, amount, blockage and source freshness are derived at read time. Historical actor attribution uses existing audit events/decisions, not invented owner history.

## Membership

The enabled typed link tables are `CaseCommitmentLink` and `CaseProposalLink`, with tenant/case/object composite FKs. Owned commitment membership is explicit; return-to-fulfillment related membership is derived through the announcement's original commitment. There is no CaseReturnLink or stored role column. Prefer deriving reservation/movement/line/source relationships through commitments rather than duplicating their links. Goal anchors need no duplicate membership row. Additional object types require a proven policy; no unchecked generic object-ID bucket.

CaseProposalLink records the bound control revision for each directly affected case and the existing proposal ID, uniquely per tenant/case/proposal. Relevant business-state digests remain in the existing canonical proposal review; avoid a second frozen-action system. Proposal links authorize nothing themselves.

## Adoption and checkpoint

A tenant-scoped `CaseAdoption` retains enabled policy set, capture boundary and exact selected historical roots under a confirmed activation decision. `CaseConsumerCheckpoint` records policy version and last incorporated event sequence. Processing failure metadata stays on the existing ScheduledJobRun. These are needed to resume/replay atomically and avoid silently taking over old work. Shared job run remains execution/retry authority; do not duplicate leases or queue state.

Control request idempotency uses existing retained ChangeProposal decisions and receipts where possible; do not add a second request journal. Case control events record actor/reason and revisions in BusinessEvent. Explain reads join authoritative objects and actual execution receipts. A cancellation request is not a cancellation confirmation.

## Schema proof

| Persisted concept | Proven use |
|---|---|
| Goal identity/typed anchor | Deduplicate many events and preserve identity after corrections |
| Control mode/member/revision | Immediate takeover, concurrent execution refusal and exact handback |
| Owned/related membership | Stop scoped work without stopping unrelated shared demand |
| Proposal case/revision binding | Multi-case action validity and obsolete-generation refusal |
| Adoption boundary/selection | Start with new work and opt into old outstanding objects |
| Event checkpoint/policy version | Atomic restart and deterministic policy upgrade |

No stored business balances, copied source totals, workflow node graph, external credentials or provider transport state. Follow existing indexes and lock ordering; tenant-crossing references fail at the database boundary as well as services.

## First-slice refinement

The concrete two-family implementation proposal in [contracts/first-slice.md](contracts/first-slice.md) governs the first slice: five tables, no separate CaseReturnLink/related-case table because return→commitment→order already provides the true relationship, and no executable refund kind or refund anchor column. Earlier broader examples are future extensions only. Actor attribution and exact control receipts use existing decisions/events. The concrete schema/domain proposal was approved by the owner in this session.
