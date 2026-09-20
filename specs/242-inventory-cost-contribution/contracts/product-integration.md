# Proposed product integration contract

Status: design prepared after the owner's authorization to qualify load and plan
integration. No production service, schema, catalog entry or permission has been
implemented by this document. The experiment and its measurements do not approve
the complete product architecture. Requirements remain those of [spec.md](../spec.md).

## Decision and existing seams

Use one Decimal costing kernel, one tenant-scoped application service and disposable,
indexed observations. Operational detail, reporting, tools and exceptions consume
the same observations and coverage rules. The prototype is evidence for this choice,
not a production persistence layer.

All paths below are repository-relative. New paths are explicitly marked proposed.

| Existing seam | Observed behavior | Proposed extension |
|---|---|---|
| `packages/reality-core/src/reality/services/finance/components.py` and `db/components.py` | Received amounts retain evidence identity; cost-center assignment parts require positive shares | Reuse received financial components. Introduce separately reviewed, signed receipt/service/selling-cost attribution; do not reinterpret cost-center parts |
| `packages/reality-core/src/reality/services/analytics/derivations.py` | Fixed allowlist declares a typed relation, identity and anchor | Register cost relations explicitly; retain the allowlist and tenant validation |
| `packages/reality-core/src/reality/services/analytics/compile_sql.py` | Service measure sources are refused; derived nodes join a base-table anchor; execution passes only limited snapshot context | Add explicit costing context and grain support before advertising measures; YAML alone cannot enable DB1/DB2 |
| `packages/reality-core/src/reality/services/analytics/inventory_relation.py` | Current inventory materializes Python rows with a 100,000-input ceiling | Do not route million-movement valuation through this relation or merely increase its ceiling |
| `packages/reality-core/src/reality/services/projections.py` | Event-type dependencies, projection checkpoints and read-only freshness; builders replace whole named projections and readers may load all rows | Reuse metadata semantics and dependency catalog, but provide indexed scoped storage and bounded SQL page/count/aggregate queries |
| `packages/reality-core/src/reality/services/projection_jobs.py`, `jobs/handlers/projections.py`, `jobs/runner.py` | Shared durable queue, internal authorization, repeatable-read projection work and fenced publication | Extend this subsystem with bounded costing work; no second queue, browser timer or API-process worker |
| `packages/reality-core/src/reality/services/exceptions.py` and `services/exception_inputs.py` | Canonical exception derivation, identity and input sharing | Consume canonical cost findings; do not independently replay FIFO per exception class |
| `packages/reality-core/src/reality/services/memberships.py` | `require_owner` uses existing company membership | Recheck active owner at financial-decision preview and execution |

## Canonical service and result contract

Proposed modules are `domain/costing.py`, `services/costing.py` and
`services/analytics/costing_relation.py`, beneath
`packages/reality-core/src/reality/`. Final implementation tasks must prove each
public entrypoint and register tenant isolation before adding it.

The application service accepts an explicit tenant, supported scope, effective cutoff,
knowledge cutoff and policy/profile revision. It returns exact decimal strings,
currency, base unit, independent coverage, source references and a freshness envelope.
The proposed operations are bounded order explanation, inventory page with filtered
totals, contribution query, trace pagination and financial-decision preview/execute.
Read operations use `no_autoflush`, never enqueue/rebuild, and never commit.

The kernel consumes ordered, evidenced inputs; it knows no ORM, permissions, browser
or queue. It implements the approved signed allocation, cumulative half-even rounding
and return-time rules. The service resolves retained evidence and policy once, calls
the kernel where necessary and owns query limits. Every adapter calls this service.

Prefer a completed indexed generation for ordinary reads. A bounded direct order
derivation is permissible only when its input bound, snapshot consistency and response
budget can be proved before replay. An old order can depend on a large FIFO prefix:
an order-ID filter alone is not a bound. If unavailable, return explicit pending or
unsupported scope, never launch a tenant reconstruction from a read.

### Relation grains

| Relation | Grain and keys | Numeric semantics |
|---|---|---|
| Contribution | One disjoint matched fulfilment/revenue slice, including explicit correction or return slices; tenant and derived slice key within a generation | Received net revenue, consumed acquisition/direct-service cost, attributable selling cost, DB1 and DB2; separate coverage for each |
| Inventory valuation | Item, economic ownership pool, currency, base unit and valuation cutoff within a generation | Physical/economically owned quantity, known acquisition subtotal, independently supported carrying value and uncovered quantities |
| Cost findings | Existing subject record plus class and causal scope within a generation | Missing basis and stale review causes; no second cost computation |

Contribution rows may carry disposable grouping keys resolved from the shortest true
links. They are not new authoritative FKs on documents or movements. Missing order,
customer or channel remains an explicit unassigned bucket. Customer/channel semantics
must declare whether retained transaction attributes or current master labels are used;
do not claim historical master-data reconstruction where no history exists.

The current anchor-based compiler is insufficient for an arbitrary many-slice node.
Extend the derivation interface narrowly to support a validated SQL selectable at its
declared grain, with tenant scoping and cutoff/generation context. Do not serialize all
contributions through `jsonb_to_recordset`. Add cardinality checks that refuse fan-out
before allowing joins to receipt components, invoices or shipments.

DB amounts aggregate only disjoint compatible slices. Aggregate coverage alongside
known subtotals; missing values must not disappear through SQL `SUM(NULL)`. DB rates
are ratios of compatible aggregate amounts, not sums or averages of row rates.
Inventory is non-additive across dates. Mixed currencies, unsupported unit conversions
and unmatched revenue/cost remain explicit partitions or refusals. A current-only
cache cannot answer a historical-knowledge query by relabeling its timestamp.

## Dependencies, invalidation and publication

Use `packages/reality-core/config/business_event_catalog.yaml` and
`packages/reality-core/config/projection_catalog.yaml` for executable dependencies.
Unknown event types retain conservative invalidation. Scoped optimization must never
drop the existing conservative correctness fallback.

| Changed retained input | Minimum affected derivation scope |
|---|---|
| Receipt, issue, return, correction or chronology | Affected ownership/item/currency/unit pools from the earliest affected sequence; include linked return descendants |
| Component, signed attribution, tax/FX/unit decision or purchase discount | Every target pool and direct-cost slice reached through that assignment; replay downstream consumption and returns |
| Revenue evidence or fulfilment matching | Affected disjoint contribution slices and their grouped totals/findings |
| Method, opening basis or economic ownership | Complete affected valuation scope, including any old and new pools |
| Selling-cost allocation or commercial profile | Affected contribution slices and DB2 coverage |
| Valuation assessment or recovery | Carrying-value reconciliation; acquisition cost and commercial DB remain distinct |
| Completeness declaration or later relevant evidence | Review coverage/findings; preserve the old reviewed basis |

A scoped dirty set needs event subjects or a retained dependency index; today's
event-type-to-projection-name mapping alone cannot prove its completeness. Any proposed
storage for this index requires explicit schema proof. A global checkpoint may advance
only when **all** affected scopes through its target watermark have been published.

Freeze the input event watermark, effective/knowledge cutoffs, algorithm and policy
versions for a build. A response reads one compatible generation manifest for rows,
counts, totals and freshness. New business commits after that watermark show pending
lag immediately; they cannot be covered by a builder that never read them. Failed or
cancelled work leaves the previous completed manifest intact and visibly stale.

The shared scheduling contract has a 30-second child timeout and 20-second statement
timeout, whereas the full reconstruction target is 120 seconds. Therefore the product
design must split reconstruction into bounded pool work and an atomic final manifest
publication, using the existing queue and claim fencing. Incomplete staged rows are
unreadable; retries are idempotent and may reuse only outputs with the exact frozen
input/version identity. A later-input race schedules another generation, not a silent
change to the frozen one. Do not increase global worker timeouts to hide this mismatch.
The bounded-worker experiment below now proves the thin staged approach locally.
Production storage/history and actual runtime registration still require architecture
review and integrated qualification; the experiment does not approve those changes.

Reuse existing metadata states `uninitialized`, `pending`, `ready` and `failed`, plus
processed/target event sequences, completion time and projection version. Extend the
response with its actual cutoff and policy/profile identity. Freshness describes the
derived snapshot; independent evidence coverage describes what is known. `ready` does
not mean complete acquisition cost, approved accounting policy or fresh upstream data.

## Evidence, financial decisions and surfaces

Trace from a contribution slice to matched movement and revenue evidence, from the
consumed layer to its receipt and attribution, and from each component to its retained
document/line and SourceRecord payload. Reuse existing movement/commitment links.
Return provenance references the original consumed slices, including a split across
cost layers. Source amounts and policy decisions remain authority; derived generation
rows never become Facts or substitute purchase invoices.

Financial preview freezes the exact proposed assignment/decision, referenced evidence
revisions, policy versions and allocation residuals. Execution rechecks active owner,
tenant scope, current revisions and idempotency in the same transaction. Demotion,
changed evidence or stale preview refuses without partial writes. An agent can execute
only the owner's explicit confirmation; infrastructure can rebuild observations but
cannot approve attribution, zero/not-applicable, tax, FX, ownership or impairment.

Add proposed `tools/costing.py` adapters through the existing tool dispatch and MCP
catalog under `packages/reality-core/src/reality/mcp/`. CLI, web and Chat use these
shared services; no ORM access or alternative formulas in adapters. Update
`config/tenant_isolation_catalog.yaml`, command/view/projection/event catalogs and
`config/resource_catalog.yaml` with the required German labels. New first-class
retained records require one consistent Inspector resolver and opaque IDs across
surfaces under FR-027; exact production entities remain subject to schema review.

Extend `config/reporting_graph.yaml`, `services/analytics/reports.py`,
`services/analytics/graph_model.py`, `services/analytics/traversal.py` and
`web/analytics_api.py` through their existing saved-analysis pipeline. Bump catalog/model
version when semantics change, and validate saved analyses against supported grains
and cutoffs instead of silently changing their meaning. Do not advertise selectable
measures before the canonical relation and refusal tests exist.

Register the following proposed classes in `config/operational_exception_catalog.yaml`
and the existing Exceptions and Rules register. Every entry needs authority, derivation,
clearing conditions, cause IDs and executable evidence under the existing contract.

| Class | Existing subject kind | Proposed severity and accountable owner | Clears when |
|---|---|---|---|
| Missing acquisition cost | `movement` for the affected receipt | `high`; Purchasing, with accounts payable | Required evidenced basis or authorized applicable declaration completes that scope |
| Unassigned cost component | `document_line`, or `document` for header evidence | `normal`; Accounts payable | Reviewed assignments account for the relevant amount without duplication |
| Stale cost review | `item` for inventory scope, `document` for an order scope | `normal`; the owner responsible for the financial review | Active owner reviews the current basis again |
| Negative actual DB1 | `document_line` for the matched sale scope | `high`; Sales management, with purchasing | Current supported actual DB1 is no longer negative, or corrected scope no longer qualifies |

The class ID/name details remain proposed until catalog validation. Existing
`sold_below_purchase_price` retains its price-comparison meaning. Incomplete DB1 cannot
be called negative actual DB1. Pending generations cannot clear findings as if current;
the queue and detail page expose the same freshness and causal evidence.

## Staged tests and release gates

1. **Kernel and evidence service:** port fixtures A-I and precision/return proofs from
   the experiment; test partial matching, signed credit, tax recoverability and missing
   basis. Observe failures before implementation. Verify value conservation independently
   of report grouping and exact prior-knowledge replay.
2. **PostgreSQL authority and authorization:** same-tenant composite links, active-owner
   preview/execute, demotion and revision races, idempotency, concurrent assignments,
   rollback and evidence immutability. Every public core function enters the tenant
   isolation catalog and coverage matrix.
3. **Projection workers:** extend `tests/test_projection_jobs.py` coverage for bounded
   parts, input races, timeout/retry, stale claims, two competing builders, worker outage,
   restart and atomic final publication. Compare incremental output with an independent
   complete replay. Test cross-pool returns and late costs, not only a single receipt.
4. **Reporting and tools:** prove compiler grain and fan-out refusals, correct currencies,
   unit/time partitions, coverage-preserving aggregation, ratios, historical cutoffs and
   saved-analysis validation. Same fixture must yield identical values and provenance
   through order detail, analysis, CLI and MCP. Reads must produce no writes or jobs.
5. **Exceptions and demo:** extend `tests/operational_exceptions/test_derivation.py` with
   the four classes and clearing/staleness cases. Reuse the canonical company/demo
   contract for one fully evidenced fixture-A business story; do not seed a second
   costing authority or bypass source interpretation.
6. **Integrated qualification:** run fixture J against actual service/reporting/exception
   and worker entrypoints in the specified combined resource envelope, with five readers,
   concurrent changes, cold/missing/stale states and serialized responses. Prove all
   FR-018 budgets, generation consistency and update visibility. A SQL-only prototype
   timing cannot pass this integrated gate.
7. **Release checks:** full required backend/frontend/migration/tenant/spec gates for
   the implemented scope, `make docs-generate`, `make docs-catalog-check`, rollback
   review and domain/architecture review before claiming production readiness.

Production migration design follows successful qualification of the storage and worker
approach. Deleting disposable observations must be recoverable from retained evidence;
rollback must preserve authoritative financial decisions and refuse destructive loss.
This document supplies the integration design, not evidence that these future gates pass.


## Implications observed in the capped prototype

The first v3 experiment held a tenant lock throughout replay. That delayed input commits
under concurrent load even when read latencies met their budgets. The corrected prototype
freezes its append-only adjustment revision, calculates without blocking intake, then
locks only for publication. The product equivalent must use retained source versions and
fenced generation publication; it cannot copy the experiment's adjustment-only shortcut.

The prototype conservatively marks every read in a tenant stale while any changed pool
is pending. That preserves correctness but can reduce live-tool availability under
continuous changes. Production live detail should determine freshness from the exact
requested dependency scope, with a bounded canonical direct fallback where proven. An
unaffected order must not inherit unrelated pool lag. Aggregate reports must still use a
compatible manifest for their whole requested scope; per-pool currentness alone cannot
justify combining incompatible cuts. Add an acceptance test with a continuously changing
pool and an unrelated order, plus a report spanning both, and measure actual ready-answer
availability alongside refusal latency. Fast `not_ready` is not a successful margin answer.

Approval sequence: qualify the thin experimental storage/worker approach and review the
production schema first; then implement the authorized slices and run integrated adapter
and release gates. Full product integration is a release prerequisite, not a requirement
to implement unapproved production schema during the architecture experiment.


## Scoped live-read prototype follow-up

The next experiment implements the proposed order-scope distinction without adding
production schema: immutable v3 movement/attribution/matching inputs plus append-only
adjustments define its dependency set. A receipt adjustment can affect an order when
its receipt lies in that order's pool prefix; a selling adjustment targets that order.
Unknown assignment targets invalidate conservatively. Scope currentness is assessed in
one repeatable-read snapshot and does not advance a global checkpoint.

A pending affected order can use the existing kernel after limit-plus-one preflight:
5,000 movement inputs and 20,000 combined financial/matching/adjustment inputs. Exceeding
these bounds refuses before replay. Successful direct reads publish nothing, schedule
nothing and retain missing evidence as null contribution. Responses identify projection
versus direct basis, assessed input revision and the still-older global published revision.
These experimental counts are not approved production resource limits. Product bounds
must include all supported source/version/cross-pool dependencies and query deadlines.

The load protocol deliberately sends half the live probes to the last order in the hot
pool, so availability cannot appear healthy simply because random samples miss the
changed scope. Both current answer count and direct-route count accompany timings.
Aggregate inventory/monthly/attention reads retain whole-generation stale semantics;
no incompatible per-pool generations are combined by this order-only experiment.

An unresolved late assignment is not merely a dirty known pool: it prevents establishing
an exact dependency scope. The prototype explicitly refuses `unresolved_dependency` even
when a direct calculation of the known rows would be small. This must remain distinct
from ordinary stale-but-resolvable evidence and from independent evidence completeness.

## Bounded shared-worker prototype

The isolated adapter now uses the existing queue, claim authorization, child watchdog,
transaction settlement and retry path. A static benchmark bootstrap temporarily binds
`projections.refresh` only inside the experiment; normal startup rejects its costing
configuration. Public queue/control tables are created only in a guarded disposable
benchmark database. No product migration or runtime handler registration is added.

Each generation freezes the append-only adjustment revision over immutable fixture
inputs. Whole inventory pools are packed into ranges of at most 50,000 movements;
an indivisible larger pool is refused. A child handles at most three ranges, with a
10-second reserve check between ranges, under the existing 30-second child and
20-second statement limits. Range rows and the cursor commit together. Retrying an
aborted transaction cannot expose or duplicate partial work. Final count checks and
an atomic pointer switch publish the entire generation. Previous generations remain
readable while work is staged; repeatable-read callers see matching metadata and values.

The typed SQL relation at issue/return grain serves experimental order and monthly
reads with null-preserving contribution coverage. It is not yet registered in the
actual reporting compiler, MCP catalog or exception derivation. Fixture source-history
bounds, retained-generation cleanup, oversized production pools, workload fairness and
production authorization still require explicit integration design and verification.


## Concrete adapter delivery follow-up

[Adapter delivery](adapter-delivery.md) now specifies the actual compiler extension,
context/result shapes, coverage-aware sums and rates, saved-analysis semantics, detail
tools and shared exception page/count integration. It supersedes generic implementation
suggestions above where it is more specific. The production source/history/storage
prerequisite and reference-host qualification remain open; no public adapter is shipped
by this design document.
