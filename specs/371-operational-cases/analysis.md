# Pre-implementation analysis of the first slice

**Date**: 2026-10-05
**Mode**: Author cross-artifact review; not independent human product/schema approval.

## Findings and resolutions

| ID | Severity | Finding | Resolution / disposition |
|---|---|---|---|
| A1 | HIGH | Earlier summary described three active families although first recommended slice only enables two | first-slice.md explicitly enables fulfillment/announced return and leaves executable refunds unavailable |
| A2 | HIGH | Order/announcement anchors cannot cover real exchange/unannounced-return entrypoints | Explicit unsupported autonomous coverage; preserve human/evidence operations; future typed anchor extension |
| A3 | HIGH | Proposal actor_type could falsely classify human-confirmed agent proposal as automation | Execution context resolved from real principal/channel/mandate; no actor_type or confirmation-boolean shortcut |
| A4 | HIGH | Generic execution claim commits before business handler, releasing locks | Guard both before durable claim and at effect boundary; already claimed work remains visible until reconciled |
| A5 | MEDIUM | Proposed broad return-link model duplicates available authoritative root relations | Minimum first-slice schema derives return→commitment→order links; no redundant related-case table |
| A6 | MEDIUM | Background consumer alone cannot stop a queued/direct action | Immediate synchronous current ownership/state checks remain mandatory at all enabled boundaries |
| A7 | MEDIUM | Historical receipt enrichment could rewrite immutable facts | Add read-envelope associations only; preserve underlying receipts and executed replay |
| A8 | MEDIUM | Test infrastructure assumed available | Local PostgreSQL endpoint refused; establish isolated test DB before meaningful failing proofs |

## Requirement and task coverage

19 FR/DR requirements have test and implementation task mapping. FR-013–016 specifically cover discovery, controls, docs and canonical ingress/claim paths. Initial 49 source-symbol inventory is populated; runtime producer, lower-write and adapter proofs are now present; exact results are recorded in quickstart.md. There are no unaddressed CRITICAL document-consistency findings after the concrete dispositions above. This is not a claim that implementation is safe or complete.

## Constitution gate

The proposed design preserves the source/evidence/reality chain, derived business state, typed tenant-scoped references, existing approval authority and shared services. New schema is justified by ownership, races, multi-case binding and durable replay scenarios. Repository constitution states self-review does not replace human approval for schema expansion. After this author analysis, the owner approved the concrete five-table proposal in chat ("ja gebe ich frei", 2026-10-05). Runtime work therefore proceeded under the recorded human authorization. Final verification and release approval remain distinct.

## Next execution order

1. Owner/domain review of the five-table first-slice proposal in contracts/first-slice.md.
2. Establish isolated PostgreSQL test infrastructure and observe meaningful failing first-slice tests.
3. Domain/model/migration and canonical atomic ensure; synchronous bindings/guards and takeover/handback.
4. Bounded event reconciliation, additive adapters/UI and generated documentation.
5. Full required backend, migration, frontend/catalog/CI checks and final review.
