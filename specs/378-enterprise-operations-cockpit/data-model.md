# Proposed shipping input model

**Date**: 2026-10-06
**Language**: English
**Approval**: Approved by the owner in chat on 2026-10-06 ("I like all of it, approval"); implementation authorized. Runtime verification remains pending.

## Purpose and smallest true links

The new records retain stated scheduling inputs, not fulfillment/forecast state. SourceRecord → accepted shipping-plan statement/requirements/capacity evidence → existing Commitment → its existing order, physical Movements and Shipment observations. Planning evidence does not create new delivery promises. No Document type or duplicate order/document-line FK is needed for this internal statement.

Use three tables. Planned times on requirements provide the Soll series; a separate curve-point table is unnecessary. Existing Location is an explicitly selected dispatch location, not an inferred warehouse hierarchy. CompanyTimeZone supplies the company business-day context. A site time zone is explicitly stated on each plan, so no global site table is needed.

## 1. shipping_plan_statement

An immutable accepted version of one internal planning stream. Its original payload remains a SourceRecord. Revisions create new Source and typed statement/child rows; nothing edits historical statements. The stream's external_id is a generated opaque plan identity, not a human label. Current accepted version is resolved through that source stream; a newer unresolved relevant source blocks dependent completeness claims.

| Field | Meaning and repeated use |
| --- | --- |
| tenant_id, id | Composite opaque identity; tenant query isolation |
| source_record_id | Same-tenant FK; unique accepted target per Source version; shortest raw-payload/exact-version trace |
| statement_kind | Source-stated `plan` or `withdrawal`; selects current planning input without inventing an operational completion status |
| dispatch_location_id | Same-tenant Location FK; explicit physical stock-exit location for this site's cohort and capacity |
| business_day | Company business date; day selection and uniqueness of current site scope |
| business_time_zone | IANA company-day zone explicitly stated by this plan and checked against CompanyTimeZone at acceptance/read; preserves the plan's day meaning if settings later change |
| site_time_zone | Valid IANA zone stated by the plan; local cut-off display and validation |

One current accepted planning stream per company/day/dispatch location is admitted. Two independent current streams for that same scope refuse completeness rather than selecting the newest by convenience. A new review replaces the exact prior version of its own stream. Withdrawals create a new Source and typed header with statement_kind=withdrawal and no children, not row deletion; they remove the stream from current inputs and leave history available. Plan statements require nonempty requirements; withdrawals must not contain requirements or capacity.

Indexes: tenant/day/location, tenant/source. Acceptance actor/time are read from the retained proposal/event authority, not duplicated as business fields. A company-zone change that conflicts with the held plan marks its day coverage unresolved until review; no silent calendar reinterpretation. No stored target totals, active-work counts, readiness, completed status, risk, observed revenue or forecast.

## 2. shipping_dispatch_requirement

One source-stated full dispatch requirement for an existing accepted customer-delivery commitment. The parent statement supplies day/site/source. The commitment supplies its shortest order/line/item/unit relationships.

| Field | Meaning and repeated use |
| --- | --- |
| tenant_id, id | Composite opaque child identity |
| statement_id | Same-tenant shipping_plan_statement FK |
| commitment_id | Same-tenant existing Commitment FK; quantity/evidence/order joins |
| quantity | Decimal quantity explicitly stated by the planning input, in the commitment's canonical unit; compare with current accepted terms |
| dispatch_due_at | Explicit UTC shipping deadline, distinct from customer arrival; deadline cohort/risk |
| planned_handover_at | Optional stated UTC planned completion instant; timed Soll; absent means unknown timed plan |

Unique per statement/commitment. In v1, one current requirement covers the full declared non-cancelled quantity of a commitment and assigns it to one day/site. A single commitment cannot be split across multiple current planning requirements. An order with different commitments at different sites is supported. This admission avoids inventing a movement-allocation identity or attaching unstable mutable OutboundDeliveryLine IDs.

The quantity is a new stated scheduling value, never a recomputed replacement for the source's value or for the original commitment. Acceptance compares it with the exact canonical commitment terms reviewed by the actor. A later quantity revision or incompatible site/meaning invalidates dependent coverage until a reviewed plan revision; the service does not silently rewrite quantity. Full cancellation excludes the work with an explicit reason, leaving the original input intact.

Constraints: positive Decimal quantity; real customer_delivery commitment; dispatch_due_at falls in the stated company business day; planned time, if supplied, has dispatch meaning and is not after its stated deadline. Unknown unit conversion refuses admission. No duplicate document_id, document_line_id, item_id, location_id or source_record_id on the child.

## 3. shipping_capacity_window

A source-stated plan-specific completion budget and collection context. It is an input statement, not a provider execution receipt or a generic transport-capacity model.

| Field | Meaning and repeated use |
| --- | --- |
| tenant_id, id | Composite opaque child identity |
| statement_id | Same-tenant parent plan; exact declared work mix/site/day |
| starts_at, ends_at | UTC capacity interval; model scheduling and time checks |
| collection_cutoff_at | Stated final collection deadline within the interval; forecast boundary and visible cut-off |
| completion_slots | Nonnegative integer capacity stated for complete site-cohort order-work units under this plan's declared mix |
| confirmation_state | Stated `confirmed` or `requested`; baseline admission and disclosure |
| confirmation_source_record_id | Same-tenant exact original confirmation Source; required for confirmed capacity, with accepted interpretation in the plan review |

The unit is a closed v1 contract: one slot completes all still-required commitment quantities for one order in this plan's selected site/day scope. It is not one package, piece or labor hour. The input must explicitly reserve/declare this capacity for this work mix; a raw carrier package limit cannot be relabeled. No implicit conversion field is added. General resource scheduling and order-weight models remain outside v1.

Windows of a current plan must not overlap; ends_at > starts_at; starts_at < collection_cutoff_at ≤ ends_at. Confirmed windows require current attributable accepted confirmation meaning, not merely a foreign-key ID. Newer unresolved/revoked confirmation evidence blocks that capacity. Requested windows remain visible but add no baseline capacity. A correction is a new reviewed plan/source version, never an update of historical capacity.

## Governance, validation and transitions

1. An authorized active company owner, or an explicitly existing applicable mandate, proposes an exact internal planning statement through shared application tools. This design does not grant a new agent mandate.
2. Preview resolves all same-company identities, dispatch meaning, canonical commitment quantity/revision, current plan source, source coverage and confirmation meaning. It reports exact payload and effects; no records are written by a read.
3. A human confirmation binds that exact review with a stable request key. Execution rechecks current authority and business/source versions under existing locks, records the immutable source/typed evidence and emits a business event in one transaction.
4. Retry returns the original receipt without overwriting a later plan. Changed payload with the same request key refuses. Revision/withdrawal requires the exact current prior plan source version.
5. New external captures use the normal source/interpretation/decision path. Unaccepted raw payload does not become a usable plan merely because it matches a shape.

No direct ORM writes by Chat/CLI/API. Proposal/event history retains acceptance audit metadata; no planning acceptance changes stock, fulfills a promise, adopts a case or contacts a provider.

## Schema proof

Every new typed business field is repeatedly selected, joined, constrained or calculated: day/site/zone define scope; commitment/quantity define compatible contents; planned/deadline times define series/risk; capacity/time/confirmation define the forecast. Other supplier/WMS/carrier payload fields remain losslessly raw and are not promoted just to display them.

Composite same-tenant foreign keys and database constraints protect child/parent/source/location/commitment boundaries. Review-level constraints additionally protect active-stream conflict and current source meaning. Exact SQLAlchemy/Alembic code follows approval; no columns are added to Documents or existing case state.

## Implementation approval record

- Product scope: approved by owner, 2026-10-06.
- Concrete three-table model: approved by the owner in chat on 2026-10-06.
- completion-slot-v1 policy: approved by the owner in the same 2026-10-06 approval.
- Shipping-input mappings, migration 0146 (following current-main default coordination 0145), closed validation, immutable reviewed acceptance and proposal adapters implemented. New foundation proofs pass; full regression verification is in progress. Shipping read assembly, cockpit UI, live lifecycle and Agent overview remain pending.
