# Integrating accepted work with operational cases

Read the [implemented feature contract](../../features/operational-cases.md), [v1 event policy](../../../specs/371-operational-cases/contracts/event-policy.md) and [entrypoint coverage](../../../specs/371-operational-cases/contracts/entrypoint-coverage.md).

Transport stores the original payload unchanged. Normal preparation freezes interpretation; exact authorized acceptance creates canonical commitments or ReturnAnnouncements. Their shared producer leaves ensure the case in the same transaction. Do not create a case at raw webhook arrival, preparation, item/location creation or from a successful refund notification. Never construct order identities from human numbers or external correlation values.

Existing object/proposal/receipt reads add `case_ids` through `object_cases`; return explicit empty associations for unadopted history. Add discovery through typed authoritative references, preserving the original fields and immutable receipts. The internal consumer only matches accepted work and records its cursor. It must never call a provider, interpret raw payloads as accepted truth or reset ownership.

All automatic writers use server-observed execution context and the shared case guard at actual effect/claim boundaries. Bind every directly affected case when preparing an existing-goal proposal. Preserve the frozen binding and business-state review during retry; never refresh an old generation. Keep the existing exact intake/delivery/business reviews. A human repair is distinguished through the authenticated decision boundary, not a caller-provided `automatic=false`, actor label or token assertion.

Future provider dispatch needs its own reviewed claim/report protocol and uncertainty reconciliation. A final pre-dispatch check can prevent new obsolete starts; it cannot undo a remote action already accepted. Declare required Source streams and reject known unresolved newer relevant versions. Missing capabilities stay unavailable rather than implying synchronization.

Migration `0144_operational_cases` adds five coordination tables. Downgrade is refused once adoption history exists. Never erase history or silently disable guards to make rollback succeed. Apply migrations as deployment work; scheduler/worker startup performs no DDL. Release requires the complete verification set and committed-head CI; local checks alone do not assert production readiness.
