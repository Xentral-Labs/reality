# Reviewed bounded inventory service

Approved continuation of production-data-model.md, not a replacement for its full scope.

## Authority and storage

- `cost_policy_revision`: item, economic owner Party, FIFO method, currency, base unit,
  zero-opening history start, predecessor/revision, confirmed action/event and reason.
  The latest revision is selected only by an explicit new review; historical reviews
  retain their exact policy. No generic automatic method resolution is introduced.
- `cost_movement_basis`: unique Movement admission, recorded physical kind/quantity/time,
  base unit, original movement.recorded event FK and introducing admission event. Values are retained input copies, not derived amounts.
- `cost_ownership_revision`: receipt basis, full covered quantity, economic owner Party,
  evidence SourceRecord, predecessor/revision, action/event/reason. The owner confirms
  the meaning of evidence; neither Party name nor location substitutes for that decision.
- `cost_inventory_review`: exact policy FK, cutoff, target input cursor, knowledge display
  time, confirming event/action/reason, algorithm/schema version and membership digest.
- `cost_inventory_member`: review -> movement basis, confirmed semantic kind, and for
  receipt members only, exact receipt cost manifest and ownership revision. Other members
  carry no fake receipt/evidence links. Same-tenant composite FKs and unique membership.

Each review creates a policy revision and receipt ownership revisions. This modest first
scope deliberately favors explicit replay and revision identity over general effective
range queries. Scope is the whole item through cutoff, not a caller-filtered movement
subset. The policy's history start declares an empty opening; any earlier held item
movement refuses. Positive receipts, shipments and transfers only; corrections affecting
any selected movement refuse, including correction-created replacements/compensations.

## Transactions and history

Reuse cost.change's active-owner check, confirmation, tenant lock, exact proposal input,
expected pre-decision event sequence, nested rollback and replay result. Capture after acquiring the
tenant lock in READ COMMITTED; stale/pre-existing repeatable-read snapshots refuse.
Costing operations continue using cost.reviewed events with a typed operation payload.
Inventory admissions and every review input become durable in the same transaction.
The sealed target cursor is the introducing review event sequence; the action retains
the pre-decision validation cursor. Current reads compare against the sealed cursor,
so a freshly confirmed review is current. Original movement.recorded events are required
uniquely; their immutable sequence supplies equal-time ordering. Missing/ambiguous
original movement events refuse instead of substituting the admission sequence.
Reads use retained basis fields and explicit receipt manifests only. Membership hashes
include selected policy, basis values, ownership inputs and receipt-manifest identities.
No authoritative FK points to a derived layer or output amount.

Validate current receipt review plus exact attribution parity before accepting its pinned
manifest. Stock confirmation reaffirms cost completeness explicitly; an unrelated event
must not force arbitrary receipt attribution changes. Current inventory conservatively
invalidates after any later tenant event. Historical reads remain exact and disclose the
fixed economic cutoff; acquisition value never substitutes for HGB carrying value.

## Bounds, tools and qualification

Use a PostgreSQL `(tenant_id, item_id, occurred_at, id)` Movement index so the bounded
cutoff query does not sort an entire item history before applying its limit.
Maximum 100 admitted movements, 20 receipts, existing 100 receipt-attribution bound and
kernel trace cap. No unbounded live reconstruction, silent truncation or partial capture.
This is a bounded reviewed snapshot service, not the future company-wide generation.
Expose cost.inventory.get plus inventory_review in existing cost.change and MCP dispatch.
No new scheduling mechanism, browser rule or automatic setup activation.

Migration 0065 follows receipt costing 0064, preserves all existing data and refuses to
downgrade populated inventory authority. Graph coverage explicitly remains deferred.
Register data-model/resource/isolation vocabulary and regenerate command documentation.
Verify owner/member/foreign/stale/replay/rollback, receipt A conservation, late costs,
historical correction replay, scope omission, unsupported inputs, integrity and bounds.


## Joint selected-item confirmation

`inventory_batch_review` extends existing `cost.change` with 2–10 `scopes`. A scope
contains the existing inventory fields (item, owner, FIFO, currency/unit, history start,
effective cutoff, both completeness confirmations, exact receipts and economic issues).
The outer request supplies one expected event sequence and reason. Distinct items must
share cutoff, owner and currency; base units may differ and are never summed together.
The total budget is 100 movements and 20 receipts, not that budget per item.

Preview validates members in stable item-ID order through the same item admission code,
returns their individual evidence/results and rechecks the input cursor at the end.
Confirmation takes the existing tenant lock, revalidates all scopes and emits one
`cost.reviewed` event. All standard item reviews link to this same action/event and
receive its recorded_at as their common knowledge timestamp and its sequence as the
sealed cursor. Each retains its own exact policy and evidence membership/digest.

No extra batch table or common policy is invented: the confirmed action is the shortest
real joint-membership identity and retains the exact request/result. The savepoint
covers every item, policy/ownership revision and the event. A failed second member
leaves no partial admission; normal action replay returns the original response.
Workers still cannot approve financial decisions. Single-review behavior is unchanged.

The result includes action_id, effective_at, knowledge_at, event_sequence and reviews.
Each stored snapshot context additionally exposes review_action_id. Joint approval does
not imply a common atomically published cache, tenant-wide completeness or DB profile;
those remain separate T080/T081 obligations. No summed report is returned by preview
or confirmation, and no cache job is scheduled automatically.

## Evidenced specific identification

An inventory scope may explicitly select `specific` instead of `fifo`. Every economic
issue then carries one or more exact portions naming the issue movement, layer-entry
movement, original receipt movement and positive quantity. The portions for an issue must
cover its exact movement quantity, may not be duplicated and may reference only retained
layers available at that economic point. FIFO scopes reject such portions; specific scopes
without complete portions refuse. No service chooses or converts the policy automatically.

The confirmed `cost.change` action is the retained authority for these exact selections;
the existing policy revision records the selected method, while movement membership keeps
the stable physical identities. Historical replay revalidates the action input, binds the
canonical selections into the review content hash and executes the existing specific-
identification kernel. Supplier returns always require exact layer selections. Customer
returns require exact portions naming the return, original economic issue, layer entry,
original receipt and quantity; they restore original sales cost at return time without
changing the historical issue. Physical return, supplier-return and adjustment movements
are admitted only when explicitly classified by the confirmed request, and settlement
links never become cost authority. Canonical selections and return parts are bound into
the historical review hash. This adds no table or derived authority. Corrections, non-zero
openings and partial/consignment/transit ownership remain unsupported until their
separately reviewed continuations.

## Movement correction normalization

The service consumes the existing append-only `MovementCorrection` chain rather than
inventing a second correction rule. For a correction known at the review cursor, the
original movement and its exact compensating movement cancel. An optional replacement is
the sole effective movement and keeps its authored economic time; the immutable
`movement.corrected` event supplies its knowledge ordering and correction provenance.
A correction without replacement removes the original from the effective history.

Every correction member must belong to the same tenant and item, the compensation must
be the exact inverse shape created by the shared movement service, and the correction
event must identify that chain before the review cursor. Incomplete, foreign, ambiguous
or unsupported chains refuse atomically. A replacement receipt needs its own current
receipt-cost review and ownership evidence. Requests name effective replacement IDs in
issue/return/selection classifications; no classification transfers silently from the
original. The retained movement basis points at the correction event and the review hash
binds the correction identity, original, compensation, optional replacement and reason.
Earlier reviews continue replaying their frozen inputs after a later correction.

## Evidenced opening acquisition cost

Approved by the owner on 2026-09-20: one immutable tenant-scoped
`cost_opening_basis` is the retained authority for an opening layer. It links the existing
`opening_stock` Movement and retained movement basis to the confirmed economic-owner
Party, evidence SourceRecord, source-stated total acquisition cost and currency, and the
confirming event/action/reason. It has an input-schema version and same-tenant composite
foreign keys. It is not a purchase receipt and stores no derived unit cost, remaining
quantity, consumption or carrying value.

The inventory request must enumerate every opening movement through its cutoff and name
its exact evidence and non-negative stated total. Omission, foreign evidence, owner or
currency mismatch and unknown cost refuse finalized valuation; zero is accepted only when
explicitly stated. The existing movement supplies quantity, unit and economic time.
Opening layers enter the existing FIFO/specific kernel as receipt-shaped calculation
inputs, while the retained member remains semantically `opening`. Corrections use the
same normalization contract above. Historical replay binds the opening basis into the
review digest and never rereads mutable action state as a new authority.

## Partial, consignment and transit ownership

Approved by the owner on 2026-09-20: `cost_inventory_ownership_part` is the immutable
tenant-scoped allocation authority for mixed-owner inventory. Each row links one retained
review and movement basis to an economic-owner Party, evidence SourceRecord and exact
positive quantity. The complete set for every effective physical movement must conserve
its quantity exactly, without duplicate owner portions, gaps or excess. Location,
shipment state, document kind and physical custody never establish ownership.

An inventory review remains one owner pool. When explicit ownership parts are supplied,
the service retains the complete allocation but sends only that review owner's portion to
the calculation kernel. Receipt and opening acquisition cost is observed proportionally
from the retained source-stated total at read time; no allocated amount or unit cost is
stored as authority. Issues, returns, losses and transfers likewise use explicit owner
quantities, so transit preserves ownership unless a separately evidenced allocation says
otherwise. Ambiguous, foreign, incomplete or overlapping allocations refuse atomically.
Legacy full-owner reviews retain their existing exact behavior and history without rewrite.
The read result exposes the retained allocation as `ownership_sources` with movement,
owner, evidence and exact quantity so every owner-filtered observation remains directly
explainable without treating the derived proportional cost as authority.
