# Implementation Plan: Operational cases

**Feature**: `371-operational-cases` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)
**Status**: Product direction and concrete five-table schema approved by the owner on 2026-10-05. First-slice implementation present; final full-suite verification is in progress (see quickstart.md).

## Summary

Add coordination above existing Reality facts: stable goal ownership, explicit work membership, deterministic event reconciliation and pre-execution action validity. The first enabled policies cover order fulfillment and announced returns. Refund intent/execution remains unavailable until its authoritative path exists. Keep live Shopify transport separate.

## Technical Context

Python 3.12+, SQLAlchemy 2, PostgreSQL, Alembic and Pydantic v2; existing application tools, scheduler/worker, FastAPI/Typer/MCP and React adapters. Decimal and UTC remain mandatory. Consumer batches are at most 100 committed events, within existing job deadlines; progress commits with effects. No new broker, provider calls, timer or workflow framework.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Cases follow accepted facts; raw arrival only invalidates freshness | PASS |
| Reality owns operational state | Completion/blockers read authoritative commitments/movements/refund evidence | PASS |
| Proven schema only | Ownership, CAS revision, typed membership, action guards and durable cursor have explicit race/replay scenarios in data-model.md | PASS |
| Tenant/shared services | Composite FKs and scoped reads; controls through application service | PASS |
| Spec/test traceability | tasks.md maps every FR/DR to tests before implementation | PASS |
| Explainable Web | Shared explain output and source links; no browser rules | PASS |
| Received values not recomputed | No copied quantity, balance or financial amount on cases | PASS |
| Smallest design | Existing job queue/events/proposals; finite policy set, no graph-wide transfer | PASS |

PASS records the author's design assessment. The owner subsequently approved the concrete five-table proposal in this session ("ja gebe ich frei"); the pre-implementation analysis was completed before runtime changes. This authorization covers implementation, not production deployment.

## Repository Structure and Layer Changes

Planned paths (new unless described as existing):

- `packages/reality-core/src/reality/domain/operational_cases.py`: kinds, goal keys, control state, pure transition/action-validity rules.
- `packages/reality-core/src/reality/db/operational_cases.py`: coordination records and composite tenant constraints; export through existing model registration.
- `packages/reality-core/src/reality/services/operational_cases.py`: ensure/reconcile, explain, takeover and exact handback.
- `packages/reality-core/src/reality/services/case_policies.py`: closed event policy registry and authoritative goal resolution.
- `packages/reality-core/src/reality/services/case_action_guards.py`: canonical applicability discovery and synchronous pre-execution checks.
- `packages/reality-core/src/reality/jobs/handlers/operational_cases.py`: database-only consumer; register in existing `jobs/registry.py` and dispatch using shared scheduling services/runtime.
- Existing `services/core.py:emit_business_event`, `db/core.py:BusinessEvent`: retain central producer and event identity; do not embed case policy rules in emitter.
- Existing `tools/application.py`, canonical execution services and claim paths: enforce case guard at application and actual executable boundary; do not rely solely on a model-supplied case ID.
- New `tools/operational_cases.py` and `web/operational_cases.py`: shared control/read adapters using existing authorization patterns; wire into existing MCP/CLI catalogs.
- `apps/web/src/unified/OperationalCaseDetail.tsx`: responsibility, work explanation, takeover and reviewed handback; link from object screens without a second rules engine.
- Config catalogs: add case event/tool vocabulary and separate `case_policy_catalog.yaml` validated against existing business events.
- `docs/features/operational-cases.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/WEB_SPEC.md`: update only with implementation.
- Inventory found `packages/reality-core/migrations/versions/` and static head `0143_intake_review_mandates`; recheck the head during implementation before adding a revision.

## Design

### Reality flow

Shopify raw source → reviewed accepted Evidence/Reality → committed BusinessEvent → case consumer → coordination/explanation. Source arrival that is newer but not yet accepted marks affected source coverage unresolved for execution safety; it does not create commitments or complete a case.

Consumer notifications are triggers to query current authoritative state, not commands to reproduce event payload effects. Event records are transactional outbox data, not event-sourced balances.

### External correlation contract

Preserve an optional caller-supplied correlation_id unchanged through supported ingress, action context, events and responses. It identifies the external tracing context, not the internal case. Never overwrite it with case_id/action_id, and never group or authorize work by it. case_id identifies stable operational coordination; action_id identifies the existing proposal/action; causation_id retains its existing event-cause meaning. Multiple correlation IDs may occur within one case, and one correlation may span cases. Do not introduce uniqueness or identity constraints on external correlation values.

Audit the touched ingress/producer paths and add preservation tests, including distinct external, case and action IDs and absence of an external value. Do not invent a foreign-system correlation value when none was supplied. Correct proven conflicting use only in the touched paths; a repository-wide correlation cleanup is separate. Preserve historical events unchanged.

### Event and goal policy

See [contracts/event-policy.md](contracts/event-policy.md). Existing events identify candidate objects. Service resolves their current relationships; one accepted order may emit many events but has one fulfillment goal. A return announcement has its own anchor. Completed external refund evidence is not an instruction to refund. A callable refund-goal policy requires an existing explicit approved intent; absent that, expose unavailable capability, not a synthetic intent.

Policy code is deterministic and versioned. Catalog documents trigger, resolver, classification, owned objects and completion predicate. Layer-generated `operational_case.*` events are not input triggers for business-goal creation. Unknown business events advance the cursor without a new case and remain auditable as unclassified where relevant; new automated action types are deny-by-default until applicability is declared.

### Ownership and action guards

Control state is `automation` or `human`; failure/blocking/completion are derived goal observations. Takeover uses expected control revision and request key, acquires the same locks as execution guards, records actual member identity, increments revision and emits audit event atomically. Independent related cases are not recursively transferred. Initial related links are associations, not a generic directed dependency graph. Explicit policy rules reevaluate affected work without recursive ownership transfer.

Prepared actions bind every affected case and its control revision plus existing exact review/state digests. Case revision tracks control transitions, not every business event. Synchronous execution checks resolve authoritative objects, check current source coverage, ownership/revision and existing review preconditions. Consumer lag cannot grant permission. Missing binding in opted-in scope refuses agent execution. Cases may be ensured at canonical preparation using current state even before consumer catch-up; this changes coordination only and grants no business acceptance.

Takeover does not invalidate ordinary authorized manual repair. Existing executed proposal receipts remain immutable and replayable; guard checks must not reinterpret a receipt replay as a new execution. Obsolete pending work is reported with reason; do not forge execution/rejection receipts or broadly mutate existing proposal statuses. New meaning requires a fresh review, not reapproval of old payloads.

### Executing and uncertain effects

Inventory all existing governed executable boundaries in T002/T008. A claimed/sent action remains unsettled until provider/warehouse evidence establishes success, failure or confirmed cancellation. Takeover serializes new starts, not network operations already in flight. Handback exposes and refuses unresolved outcomes. Current workers have no direct external I/O: future Shopify adapters must check case ownership before dispatch and report/reconcile external outcomes through reviewed adapter contracts. Internal tests do not prove that future transport.

### Handback

Read-only preview provides exact case revision, relevant facts/source cutoff, unsettled actions, outstanding goal and gap reasons. Confirm locks current authority and case, rechecks facts and freshness and accepts only identical review. A changed source or new execution refuses without mutation. Successful handback increments control revision; remaining work is newly prepared as needed. A completed goal needs no new work. A correction can reactivate the same goal identity, but cannot reactivate an old action generation.

### Consumer, recovery and rollout

Independent checkpoint per tenant/policy version; atomic writes and advancement; shared job leases/retries/deadlines. Acquire canonical business/tenant locks before ordered case locks to avoid reversing existing lock order. Bound rebuild/bootstrap by object selection and cursor; never advance over an unrecorded policy failure. Expose progress, lag, failure, adoption state and capability gaps.

Enable per company using confirmed boundary/selection. Backfill coordination from explicitly selected current outstanding objects; preserve source history. Case controls are operational authority so cannot be casually rebuilt from facts alone: rebuild membership/observations while retaining stable IDs, controls and action links. Policy changes require reviewed migration of affected membership without resetting ownership.

### Mandatory ingress and execution coverage inventory

The static code inventory is now populated in `contracts/entrypoint-coverage.md` with 49 concrete canonical boundaries, adapter/dynamic dispatch traces and known anchor gaps. Before runtime implementation, review these dispositions and refresh coverage against actual executable command/tool catalogs, service callers and adapter routes. This is a release-blocking inventory, not a second processing channel or a blanket rewrite of all writers. Cover the three selected goal families across human Web/API, CLI, external MCP, import preparation/acceptance, internal services and scheduled workers, plus proposal preparation, execution and actual external claim boundaries.

For each reachable entrypoint record its exact symbol/path, callers, authority, accepted effect, goal/object resolver, create/match/update/no-case classification, transaction boundary, binding/guard location, test and rollout disposition. Distinguish evidence admission from business-goal creation and action execution. Refund evidence and raw source arrival never implicitly request a payout. Unsupported adapter paths are explicitly unavailable; they do not count as covered enabled paths.

Canonical accepted goal creation must ensure/match coordination in the same transaction, using current authoritative relationships and unique goal anchors. Source capture/preparation must not create accepted business goals; preparation can bind an already accepted goal. Events retain replay/recovery reconciliation without duplicating cases. An agent executing through a lower-level reachable service or claim path cannot bypass ownership/state checks by omitting a case ID; every enabled automatic effect is server-classified and guarded. Authorized human repairs retain existing business authorization and do not receive the automation-only ownership refusal.

The enabling gate is zero unclassified reachable paths in adopted scope and a passing meaningful proof for each enabled create/match or automated execution boundary. Explicit no-case classifications require rationale. Verify direct lower-level calls as well as UI/MCP adapters, multi-case actions, consumer lag, duplicate creation and transactional rollback. A static writer inventory is discovery only; unrelated subsystems and universal writer gating remain excluded.

### Existing UI, API and MCP compatibility

Inventory existing order/return/refund evidence reads, object inspectors, proposal reviews, execution receipts and MCP response schemas before implementation. Add `case_ids` (an array, never a forced single ID) and object-to-case discovery through shared services. Selected case details use an opaque `case_id`. Historical/unadopted data returns an empty array; no read-time creation. Case association and control fields remain distinct from external correlation metadata. Validate model/client-supplied case IDs against canonical membership; existing object-ID inputs remain valid. Avoid exposing unrestricted external payloads or tenant data.

Use additive response changes and update strict schema consumers, projections and generated MCP reference together. Existing executed receipts are immutable: enrich their read envelope through authoritative associations rather than rewrite historical receipt JSON. Older clients tolerate missing case metadata during rollout; new clients display unavailable association state without inventing ownership.

Web supplies a discoverable case list and detail, copyable ID, object-context links, responsibility and owned/related work. Initial controls are “Take over manually / stop automation”, “Review current state”, and “Return to automation” using exact reviewed handback. Show already-started/uncertain effects and distinguish automation stop from confirmed warehouse/provider cancellation. No independent marketing/category label is introduced: the requested marking means manual responsibility, not cosmetic tagging. Use existing proposal/confirmation components; current authorization determines control visibility.

### User and maintainer documentation

Document deterministic trigger examples and repair/handback guidance in `docs/features/operational-cases.md`, the bilingual Shopify maintainer guide and user-facing integration content under `apps/docs/content/integrations/` and `apps/docs/content/de/integrations/`. Include identifier definitions, empty historical associations, scope limits and unavailable refund/fulfillment capabilities. Wire user docs through the current navigation mechanism discovered during implementation. Update executable catalogs and regenerate `apps/docs/content/tool-usage/` plus German references through the existing generator, never maintain duplicate hand-written tool schemas.

### Data and migration impact

See [data-model.md](data-model.md). Additive tenant-scoped records; no historical mass rewrite or fabricated ownership decisions. A case provides coordination, not a new order status. Rollback must not leave automated agents active while case gates are removed.

## Test Strategy and Traceability

[Tasks](tasks.md) map all requirements. Pure policy tests; PostgreSQL service/race/rollback/replay tests; business stories across order/return/refund evidence; API/CLI/MCP authorization parity; focused Web control tests. Meaningful initial failures are absent case policy, takeover controls, action guards and checkpoints. No live connector test claim.

## Rollout and Rollback

1. Migrate additive schema and deploy disabled service/read capability.
2. Observe cases for explicitly selected test-company objects with automation disabled.
3. Verify action-binding/guard coverage before enabling governed automation for that company.
4. Exercise human repair/handback and delayed-consumer races using original accepted fixtures.
5. Connect live Shopify only after the separately implemented adapter supplies required evidence and result reconciliation.

On rollback pause opted-in automation, settle outstanding execution uncertainty and retain coordination/audit rows. Older runtime may be deployed only with that automation disabled. Do not drop tables while controls or external actions remain active; review migrations for dependency-safe downgrade.

## Review Risks

- Confusing refund evidence with refund intent or claiming unavailable fulfillment coverage.
- Incomplete action/claim gate coverage, especially actions spanning several cases.
- Domain completion inferred from Shopify status instead of authoritative execution.
- Pausing too broad a business graph or resuming before external outcomes are known.

## Complexity Tracking

No constitutional exceptions proposed. A proposal-only link cannot represent durable human ownership; correlation IDs cannot enforce typed case identity; read caches cannot authorize execution. These simpler alternatives are insufficient for the specified races.

## Inventory findings incorporated (2026-10-05)

Documentless replacement/customer promises and unannounced physical returns are real existing paths, outside the initial order/announcement anchor design. Preserve authorized human repair and evidence capture. Initial adopted automation for these roots is explicitly unavailable until a reviewed anchor extension exists; never silently invent an order or announcement. Outbound deliveries may span multiple order cases. Refund ledger booking is not a provider payout-intent root. Generic proposal claim, specialized intake/finance execution, dynamic intake effect dispatch and queued batch children each require guards at their actual boundary. See the inventory for exact symbols and baseline test references. Static inventory completion does not prove runtime protection.

## Future case-family extension list

See [contracts/case-candidates.md](contracts/case-candidates.md) for source-grounded candidate goals outside the initial Shopify slice. Use the same finite-policy extension points (typed anchor, resolver, trigger classification, owned work, related impacts, completion, execution applicability). Do not implement speculative roots or broaden universal gating now. A future supplier/Finance/warehouse slice gets its own reviewed spec, canonical entrypoint inventory and tests; the current inventory is not evidence of coverage for it. Highest-value extensions are supplier-order fulfillment, invoice review and stock-block disposition, plus the already discovered replacement/unannounced-return anchor gaps.

## Concrete first-slice decisions and review

[contracts/first-slice.md](contracts/first-slice.md) narrows the enabled policy set, proposes exactly five coordination tables, derives return relations instead of duplicating them, enumerates actual atomic insertion/guard boundaries and distinguishes human-confirmed agent proposals from autonomous mandate execution. [analysis.md](analysis.md) records resolved consistency findings, requirement coverage and the recorded owner schema/domain approval. The owner accepted the implementation direction and subsequently approved the concrete schema. The authored analysis remains separate from that human approval.
