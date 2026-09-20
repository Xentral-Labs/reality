# Confirmed single-line commercial contribution

This is the next owner-authorized staged implementation of the reviewed production
model. It specializes revenue matching/context retention to the already supported
whole invoice line / whole shipment case, without a general allocation engine.

## Authority and shortest links

`cost_revenue_match_basis` retains invoice DocumentLine, billed order DocumentLine,
CostMovementBasis, item and customer IDs; received net amount, quantity, currency, unit,
invoice date and order sales channel; evidence fingerprint, input version and admission
event. Unique tenant/invoice-line and tenant/movement-basis keys prevent either full
quantity from being reused. No derived consumption or margin is stored. Order and
invoice document/source links remain reachable through their lines; do not duplicate FKs.
These context fields are exact admission copies, not an attempt at arbitrary historical
queries over mutable documents. Protect both admitted documents with the existing cost
evidence guard. General replacement/rematching remains unsupported.

`cost_contribution_review` links that basis to one exact CostInventoryMember, with
predecessor/revision, fixed commercial_v1 profile, explicitly confirmed economic time,
knowledge time, introducing event/cursor, action/reason and integrity digest. The selected
member must reference the basis's movement input and confirmed economic issue kind.
This one review is also the scoped profile approval and frozen calculation generation;
its opaque identity is used for both, not a fabricated global profile. No independent
company-wide profile activation is introduced. Future general profile/context tables
remain outside this bounded specialization. All links use same-tenant composite FKs.

## Confirmation and reproduction

Extend cost.change with contribution_review, explicit revenue completeness and profile
confirmation, current event cursor, exact candidate hash and economic timestamp. The
economic timestamp must equal the candidate shipment time and the owner explicitly
confirms revenue recognition there; do not substitute invoice/order/payment dates.
Reuse active-owner check, tenant serialization, exact proposal binding, confirmation,
nested rollback and replay. Preview and execution both validate the same current
candidate. The decision event is cost.reviewed with a typed operation payload.

Reaffirmation can change the inventory review, but cannot silently move a whole line
to another shipment or reuse its shipment for another invoice. Bindings and source
inputs remain immutable. Later accepted cost evidence requires a fresh inventory review
and new contribution review. Admitted invoice/order mutations are refused with a
contribution-specific reason; unadmitted documents retain existing behavior.

Current contribution reads require READ COMMITTED and finalize DB1 only while the sealed decision cursor is current.
Any later tenant event conservatively invalidates current output; historical review_id
reads use exact retained source inputs and the inventory member's original review, never
current document fields or a live movement scan. The decision cursor includes its own
introducing event so first reads are current. DB2 and its rate remain null with an
explicit selling-cost gap. Historical trace distinguishes retained invoice date, confirmed
economic time, knowledge time and original evidence identity. Corrupt hashes/versions
refuse, not yield a partial authoritative result. Read paths do not flush/write.

## Migration and checks

Static migration 0066 follows 0065, adds only these two tables and required FK indexes,
and refuses populated downgrade before deleting either table. No new background job,
graph measure or dedicated UI. Register public reviewed_contribution and cost.contribution.get
plus MCP, finance resource labels and tenant evidence. Keep graph integration deferred.

Test first: fixture A DB1 570 / 47.5%, DB2 unknown; confirmation/owner/exact binding,
replay, transactional rollback, demotion/foreign access, stale current versus frozen
history, source protection, source/movement uniqueness, late-cost reaffirmation, digest
corruption and migration rollback. Run full backend and relevant catalog/doc gates.


## Joint full-line confirmation

`contribution_batch_review` adds `positions` (2–10 ContributionScope objects) to the
existing cost.change command. Each scope contains the single-line candidate/profile/
revenue/economic-time/selling-category fields; expected_event_sequence and reason are
shared at the action level. Preserve one-position operation compatibility.

All candidates must refer to one actual confirmed inventory action and share its
effective_at, knowledge_at, introducing event/cursor, economic owner and currency.
The selected contribution scope may cover a subset of that action's items; it does
not claim every tenant sale or all inventory members. Each shipment basis may occur
once. Units and economic recognition instants stay per position. Current candidate
admission already validates supported inventory membership and received evidence; no
raw client amounts or fabricated shared profile revision are accepted.

Validate all members in stable invoice-line ID order before emitting the one decision
event. Existing tenant serialization and outer savepoint cover execution. The event's
recorded_at is every member's knowledge_at, included in each existing integrity digest.
Return action_id, profile_scope_action_id, profile, inventory_action_id, effective_at,
knowledge_at, event_sequence, currency, owner_party_id and ordered reviews. Individual
review IDs and profile_revision_id meanings remain unchanged. No aggregate DB totals
or quantities are returned. Missing selling coverage remains independent by position.

Historical member reads use the existing reviewed_contribution API. Later publication
will need to validate exact executed action membership before treating these reviews
as a report population; this command alone does not create a cache or canonical SQL
relation. Replaying the executed action uses existing action idempotency.
