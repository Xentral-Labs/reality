# Proposed application and UI interfaces

**Language**: English
**Status**: Owner-approved implementation design on 2026-10-06; runtime evidence pending.

## Shared vocabulary

- `shipping_plan_propose`, `shipping_plan_revise_propose`, `shipping_plan_withdraw_propose`: prepare exact reviewed internal statements, with current source/commitment/confirmation bindings. They do not execute providers or accept an unreviewed statement.
- `shipping_performance`: canonical plan/handover/forecast/cohort read.
- `shipping_supporting_orders`: full-result filtered/paged supporting orders and current basis comparison.
- `operations_cockpit`: shared assembly of shipping, supported case summaries and actual responses.
- `operations_cockpit_activity`: bounded rolling recorded-entity activity and recent events, using the existing canonical activity classification.
- `operations_cockpit_agents`: owner-authorized sanitized named access/client inventory with complete scoped totals, paged rows and attributable observed actions; does not expose credentials or assert external runtime liveness.
- `operational_case_register`: new filtered/paged canonical register; old `operational_case_list` response remains compatible.

All callers use registered application services/tools. Read tools are read-only; proposal confirmation/execution follows existing actor/mandate/preview/replay conventions. No browser-only producer, direct ORM CLI action or external-token self-approval is added. New producer authority is owner-confirmed or an already applicable reviewed mandate; this feature does not create such a mandate.

## Planning proposal payload

Capture exact original values. Closed input schema admits:

- Source-stated plan/withdrawal kind, current plan identity/prior source version for revision or withdrawal, and server-generated opaque identity for creation. Withdrawal retains a typed header and original Source but admits no work/capacity children.
- Business day, explicitly stated company-day IANA zone checked against current CompanyTimeZone, same-company dispatch Location, and stated site IANA time zone. Calendar changes do not silently reinterpret an accepted plan.
- Requirements: same-company commitment ID, stated Decimal quantity, explicit dispatch deadline, optional planned handover time.
- Capacity windows: stated starts/ends/cut-off, integer completion slots, requested/confirmed state, exact same-company confirmation Source reference where applicable.
- Stable request identity through preview/confirmation; existing reviewed-proposal execution applies, with a fresh review required after changed meaning.

The proposed UI does not add a planning workflow into the Head of Operations' normal day. Planning inputs can arrive through existing authorized source interpretation or shared tools. Initial acceptance fixtures use confirmed shared services. Any later planning editor or provider integration requires separate scope.

## Availability and HTTP reads

Normal admitted tenant authentication plus active company membership are required. Platform administration alone is insufficient; existing Engine Room telemetry access remains unchanged. A server configuration capability defaults off.

| Interface | Meaning |
| --- | --- |
| `GET /api/tenants/{tenant}/operations-cockpit/capabilities` | Authorized read of enabled state; no business action or case adoption |
| `GET /api/tenants/{tenant}/operations-cockpit?day=...&location_id=...` | Current consistent company/day/site snapshot; day accepts Today or an ISO date, and Today resolves against CompanyTimeZone on each read |
| `GET /api/tenants/{tenant}/operations-cockpit/orders` | Paged supporting orders with measure/time filter and optional prior basis |
| `GET /api/tenants/{tenant}/operations-cockpit/activity?minutes=15` | Company-wide 5/15/60-minute recorded-entity graph and latest 50 matching event identities, with coverage/observation metadata |
| `GET /api/tenants/{tenant}/operations-cockpit/agents` | Owner-only read of eligible manual credentials/client grants; bounded keyset paging and explicit access-state filter |
| `GET /api/tenants/{tenant}/operational-cases/register` | New paged register with supported kind/control-mode/outstanding filters |

Disabled cockpit data routes refuse as unavailable; capability remains readable to an authorized member so the client can return to permitted Home. Register static route must precede the existing `/{case_id}` route. Non-disclosing cross-company/unknown-ID behavior is preserved.

Snapshot includes:

- `observed_at`, company business day/time zone, selected Location, `basis_key` and observation watermark.
- Coverage by plan/cohort/site/handover/timed-Soll/capacity/forecast; known-empty differs from missing input.
- `shipping`: full cohort totals, actual/plan/future-forecast series, per-site rows, relevant site cut-offs and inspectable basis. The basis fingerprint includes the full canonical source/quantity/readiness/physical input set and exact company/day/site/calendar context. The response discloses at most 50 work/source/revision/readiness/physical records per section with complete sizes and an explicit preview marker; this limit never samples the calculation. Paged supporting orders retain exact source IDs and full canonical readiness/physical evidence. Interpretation notices are presentation text, not duplicated fingerprint inputs.
Complete registered-case counts, items and canonical coordination/kind coverage come from the existing independent case-register observation. Shipping snapshots do not duplicate that register; exact case-linked deviation evidence remains in the shipping snapshot. This separation never implies six-family company autonomy or atomicity between the independent reads.
- `deviations`: exact affected business IDs, causal records, responsibility and recorded responses/outcome/next check, only where evidence exists.

Values use returned quantity/count/money meaning; frontend does not recompute totals or infer a status. No merchandise-value/48-hour-risk or seven-day-SLA claim is added until its own canonical measure exists.

Activity returns `observed_at`, window start/end, `coverage_start`, 60-second bucket resolution, partial-boundary coverage, complete category counts and bounded recent event references with recording/occurrence times. Its canonical classification/deduplication matches Home; existing Home endpoints retain their current behavior. This company-wide read does not inherit the shipping-site filter. Each response retains its own observation basis; do not claim atomicity between independent snapshot/activity requests. See the [all-day live contract](live-observation.md) for lifecycle and presentation rules.

Agent/access read requires current company owner authorization independently of normal cockpit membership. Return coverage/observation, complete matching total, `items`, `has_more` and an opaque context-bound `next_after`, with maximum page size 50. Rows carry credential-kind-qualified identity, recorded name, connection kind, effective access state/reason, last-used time and only exactly attributable observed operation/outcome/business references. Omit secret material, prefixes/hashes and unrelated personal data. Missing runtime identity or current execution remains unknown. Non-owner panel refusal must not fail the member's other cockpit reads. Existing connection-management/telemetry routes retain their guards.

Supporting order query admits `measure=due|plan|handover|risk|forecast|unplanned`, exact selected day/Location, either a cumulative `at` instant or a half-open `from`/`until` interval within that business day, and bounded `after`/`limit` (maximum 100). Full matching totals precede pagination. Return `items`, `total`, `has_more`, `next_after`, current basis/observation and `re_evaluated` when prior basis differs. A limit or display sample never changes totals. Cursor is an opaque order key scoped to the exact filter, not a human order number.

## Responsibility register and detail

Register queries derive outstanding order IDs through canonical commitment terms and the domain goal function, then count/filter/page the full same-company register in PostgreSQL. Canonical return-state mapping governs return predicates. Closed historical orders are counted without hydrating every case or replaying historical quantity reads. Register query filters supported `kind`, `control_mode=automation|human`, optional explicit `outstanding_only`, and bounded keyset paging. Default human-owned register includes completed/abandoned supported work until explicitly filtered; responsibility is not silently removed by completion.

The protected register response includes its own `observed_at` from the same
read-only observation context, including empty or incomplete platform coverage. This is transient
read metadata, never a stored case status or business authority. Register and
Agent panels display and retain their individual observation times after a failed
refresh (FR-018 and the live contract); the shipping header's time is not reused
for independently refreshed panels. Older responses without this metadata show
an explicitly unknown observation time.

Detail additions are derived reads: current exact control decision ID, control event/revision, takeover actor/time/retained reason; actual proposal review/receipt links and unresolved source/execution gaps. If historic attribution is incomplete, report unknown. Limit embedded action rows and expose existing history navigation rather than load unbounded receipts.

Controls reuse existing Web endpoints unchanged: member-confirmed takeover with expected revision/request key/reason, current handback review and exact digest confirmation. Spec 377 default coordination applies; legacy owner-adoption records do not gate the register. Its additive `coordination` metadata reuses canonical rollout readiness, with no read-triggered rollout, adoption or authority change. A case ID must not be passed to a commitment-scoped chat helper.

## Route state and deep work

Add `/app/cockpit` and namespaced `cockpit_day`, `cockpit_location`, `cockpit_measure`, `cockpit_case`, `cockpit_basis` plus a structured allowlisted origin context. Carry that context through existing order/delivery/Inspector URLs; reject other-company origin and clear it on company switch. Do not accept arbitrary return URLs.

`cockpit_day=today` is the default and follows the current company day; an explicit ISO date stays pinned. Serialize the activity window in `cockpit_minutes=5|15|60`, independently of shipping day/site. Presentation-only stream following remains local viewport state and never changes case control. Refresh preserves open records, scroll, chat input and exact current control reviews.

Sales/detail continues through `orders_view=customer-orders&entry=<document ID>`; delivery workspace through `orders_view=deliveries&order=<document ID>&delivery_type=customer_delivery`. Inspector already supports exact target-kind/target-ID. Existing record-based chat handoff is reused with actual same-company order/commitment context.

Cockpit default panel states: shipping overview, supporting orders, supported case detail/register, human-owned work. Chat closed by default on cockpit entry; explicitly opened chat uses current business context. Genuine approval queues remain directly reachable in existing navigation, without becoming the default interpretation of every deviation.

## Failure states

Initial loading, known empty, unavailable feature/input, partial coverage, stale prior snapshot, failed refresh and refused control are distinct. No automatic acceptance/retry of an uncertain external effect. No positive readiness claim from a business curve or count of agent-owned cases. Auth loss clears company data; availability loss returns to a permitted route without changing ownership.

### Essential planning source disclosure

`basis.planning_source_record_ids` retains every exact daily-plan and capacity-confirmation Source identity. The bounded `basis.sources` metadata preview selects those identities across all sites before sampling order sources. Source metadata remains capped at fifty entries globally, full source/work counts remain disclosed, and the fingerprint is still calculated from the complete original basis. All planning IDs remain available even when essential metadata itself exceeds the preview bound. This is observation/provenance data, not stored authority or permission.

Company-wide `flows` are returned by the existing activity observation, alongside
recorded activity, with their own observation timestamp. The shipping overview
retains shipping/case/deviation evidence. Day/site changes never restart company
flow reads. These independent authorized snapshots retain exactly the existing
four read lifecycles; do not claim atomicity between them.

Shipping returns `series_resolution_seconds` per series: zero for exact event
points, 300 for exact full-cohort cumulative five-minute boundaries on dense
curves. Dense series include opening/terminal counts and retain complete basis
fingerprints and supporting-order evidence. The UI explicitly discloses the
aggregation; an interval count never asserts a new physical event timestamp.


### Primary-cohort risk partitions (FR-053)

Each existing flow area adds optional `risk`: `scope`, nullable `total`, nullable
`in_plan`, `at_risk`, `critical`, `unclassified`, and `coverage` (complete/partial/unavailable).
Known counts are disjoint and reconcile to the full displayed primary count. Order
identities collapse all open lines at their worst condition; missing delivery dates
remain unclassified unless a stronger existing finding is held. High/critical
exception severity is Critical; other held findings are At risk. Due-soon customer
exceptions are included alongside overdue/unreserved findings because they supersede
the latter. Supplier scope is open lines, stock scope only oversold items, and return
scope pending physical positions. Missing learned return findings do not establish
timeliness. Message urgency counters remain null without held deadlines, while
the complete unanswered count is unclassified; missing mailbox coverage keeps all
counts null. No financial risk observation is invented. Derive all partitions from
already loaded tenant-scoped cohorts/findings; no stored status or additional SQL.

### Stable analysis interaction (FR-057–058)

Operational instruments have no selectable state or detail anchor action. The one
labelled analysis selector controls the existing mounted area articles in place. Its
state replaces the current area fragment, preserving history state and avoiding any
scroll/focus transfer. Initial area fragments and live/company resets remain supported.
Finance keeps its explicit navigation link. API and business-control contracts unchanged.
