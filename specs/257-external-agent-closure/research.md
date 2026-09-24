# Research: External Agent Audit Closure

## Decision 1: Treat the audit as a closure matrix, not thirteen assumed defects

**Decision**: Preserve F1–F13 as traceable inputs, then close each through implementation,
guidance, regression proof, an accepted limitation or a superseded claim.

**Rationale**: The independent run found real gaps, but also treated exact-location inventory,
owner authority and evidence-based costing as missing automation. Implementing every claim
literally would violate existing approved contracts.

**Alternatives considered**: Implement every finding as reported; split the evidence across
unrelated fixes without one terminal audit record.

## Decision 2: Reuse the shared proposal review as the agent-to-owner handoff

**Decision**: Enrich proposal preparation with structured next-step metadata and send
owner-governed actions to the existing tenant-scoped Web decision/review contract. Agent
credentials remain unable to act as owners.

**Rationale**: Spec 249 and the current proposal-review service already provide the correct
principal, state-bound review, rejection and stored-input execution boundary. A second MCP
approval workflow would duplicate authority.

**Alternatives considered**: Treat the MCP token issuer as the confirming owner; return a
long-lived review token directly from every propose call; add a transport-specific finance
approval path.

## Decision 3: Add semantics to receipts, not a new reservation state

**Decision**: Derive `none`, `partial` or `complete` from existing requested/applied/shortage
values and expose remaining work and verification reads in the receipt. Keep reservation at
the commitment's exact location.

**Rationale**: Existing quantities and record/event identities are sufficient. The defect is
ambiguous presentation of zero effect, not missing stored state or missing hierarchy traversal.

**Alternatives considered**: Add reservation status fields; aggregate descendant locations;
fail every partial reservation instead of returning its real effect.

## Decision 4: Keep one canonical schema and qualify the deployed release

**Decision**: Continue deriving model schemas and generated Tool Usage from the canonical MCP
registry, strengthen schema/capability tests and add a release check against deployed
`tools/list` for names, required fields, enums and nested shapes.

**Rationale**: Local registry/docs parity largely exists. The audit discrepancy can only be
closed by proving the deployed artifact matches the checked-in release.

**Alternatives considered**: Maintain a second manual MCP reference; accept probing as normal
discovery; compare only tool names.

## Decision 5: Resolve capability aliases from registered identities

**Decision**: Capability lookup accepts the exact public name first, then a unique registered
application-tool identity, and always returns the canonical public identity. Ambiguity is
refused with bounded candidates.

**Rationale**: This makes documented capabilities discoverable without a new alias catalog or
guessing internal suffixes.

**Alternatives considered**: Hand-maintained alias map; fuzzy matching; expose internal names.

## Decision 6: Expose existing proposal rejection through MCP

**Decision**: Bind a controlled MCP rejection action to existing `reject_proposal`, require an
explicit authorized-human rejection decision, exclude the action from default model selection,
allow only pending proposals and return stable rejected lifecycle information on safe replay.

**Rationale**: Rejection, authorization, attribution and Web behavior already exist. The gap is
adapter coverage, not lifecycle design.

**Alternatives considered**: Delete proposals; leave cleanup Web-only; automatically expire all
unconfirmed proposals.

## Decision 7: Add a dedicated invoice-credit context read

**Decision**: Expose the existing invoice-credit context service through MCP, returning eligible
opaque invoice-line identities, capacity and blockers. Preserve the current complete nested
credit proposal schema and add regression coverage.

**Rationale**: A generic document-line repository read would expose too much and still would
not calculate credit eligibility. The existing derived context is the shortest useful contract.

**Alternatives considered**: Depend on creation receipts; add generic DocumentLine discovery;
duplicate eligibility logic in MCP.

## Decision 8: Add an atomic free supplier-invoice action

**Decision**: Create one explicitly human-confirmed application action that records immutable
manual supplier invoice evidence with supported free lines and posts the payable atomically. Use
ordinary mutation authority rather than adding owner-only authority. Keep the existing order-line
invoice action unchanged.

**Rationale**: The current two-step workaround is valid low-level machinery but not a coherent
agent action and can leave an unposted intermediate document.

**Alternatives considered**: Invent a purchase order; broaden the order-linked tool with
ambiguous mutually exclusive shapes; bless generic document creation as the normal workflow.

## Decision 9: Expose existing dunning rather than rebuild it

**Decision**: Publish existing dunning context/detail, record and reversal through MCP using
the existing finance proposal/owner confirmation boundary.

**Rationale**: Dunning service, Web flow, evidence and fee semantics already exist. Only the
public MCP adapter is missing.

**Alternatives considered**: Create a second dunning command; generate or send reminder
messages; model a dunning notice as an arbitrary document.

## Decision 10: Validate operational document meaning before persistence

**Decision**: Centralize the six public manual operational types (`sales_order`,
`purchase_order`, `sales_invoice`, `supplier_invoice`, `credit_note`,
`supplier_credit_note`) in the shared service, validate public action preview and derive the
public enum from the same contract. Unknown upstream labels remain losslessly stored in source
payloads, not typed as operational documents; source intake is not constrained by this allow-list.

**Rationale**: Accepting arbitrary typed documents creates business-looking artifacts that
later tools cannot interpret. Adapter-only validation would leave alternative paths divergent.

**Alternatives considered**: Keep free string and rely on posting refusal; database enum;
discard unknown upstream labels.

## Decision 11: Preserve current settlement semantics

**Decision**: Use existing finance settlement for actual cash, bounded allocation, reductions,
overpayment credit, credit allocation and refunds. Keep legacy invoice-bound payment capped.

**Rationale**: The audited missing behavior already exists behind the owner-confirmed finance
path. Loosening the legacy tool would duplicate money evidence and blur allocation.

**Alternatives considered**: Allow legacy payment above the invoice; create a fake credit note;
accept reductions without configured accounts or owner review.

## Decision 12: Add derived stage-aware costing guidance

**Decision**: Enrich the existing cost query, or a focused read service beneath it, with stages
from evidence through admission/review/publication, exact missing basis, bounded opaque scope,
permitted next owner action and explanation links. Mutations remain existing `cost.change`
proposals confirmed by owners.

**Rationale**: Current reads truthfully return uninitialized/missing codes but do not explain
how an ordinary company reaches a supported result. Derived guidance needs no persistence and
does not become financial authority.

**Alternatives considered**: Infer actual cost from price/order values; auto-confirm cost
reviews; reuse demo setup authority for ordinary companies; store an onboarding state machine;
implement wizard rules only in Web.

## Decision 13: No schema, scheduler or historical repair

**Decision**: Use existing records and user-driven proposal lifecycle. Spec 251 remains the
only demo readiness orchestration. Do not automatically clean the historical CanisPro tenant.

**Rationale**: Existing identities, proposals, evidence, reviews and generations express all
new behavior. Persisting derived onboarding or audit state would add a second authority.

**Alternatives considered**: New onboarding tables; background repair jobs; automatic deletion
of probe documents/proposals; another demo queue.

## Decision 14: Scope receipt-review freshness to canonical evidence

**Decision**: Retain optimistic concurrency for cost mutations, but decide whether an existing
receipt review remains current from a canonical fingerprint of its receipt basis, admitted
components, attributions, corrections and category decisions. Return the exact changed evidence
scope when it becomes stale.

**Rationale**: A global tenant sequence is safe but semantically false: payment terms, unrelated
payments and another item's movements cannot change one receipt's reviewed acquisition cost. The
existing retained manifest and evidence hashes provide the correct bounded inputs without a new
authority record.

**Alternatives considered**: Keep global invalidation; never invalidate reviews; copy a mutable
`current` flag onto the receipt; batch all tenant reviews after every mutation.

## Decision 15: Transfers move cost layers; they do not acquire stock

**Decision**: Model an internal transfer as continuity of the existing owner and cost layer from
source to destination. Inventory review names exact movements whose origin cannot be resolved.

**Rationale**: The transfer changes location, not ownership or acquisition evidence. Requiring new
invoice evidence at the destination double-counts the physical receipt and breaks the shortest
trace to the supplier acquisition.

**Alternatives considered**: Attribute the supplier invoice twice; ignore transfer destinations;
require an owner to confirm zero cost for every internal transfer.

## Decision 16: Use the existing lossless invoice finance envelope

**Decision**: Invoice actions accept and retain only source-stated net, tax, gross, currency and
codes in `reality_finance_v1` within the existing line payload. Missing values remain absent;
contribution consumes stated net only.

**Rationale**: The finance-component service already validates this envelope and hashes it as
evidence. Adding typed columns would duplicate received evidence, while deriving net from gross
would violate the no-recomputation rule.

**Alternatives considered**: New net/tax columns; compute net from tax rate; treat gross as net;
manual full-line correction after posting.

## Decision 17: Distinguish deterministic failure from indeterminate execution

**Decision**: Validate knowable relationships before proposal persistence. If confirmation still
encounters a deterministic domain refusal and rollback proves no business effect, retain a
terminal `failed` result with a bounded error receipt. Preserve `executing` for timeouts, lost
responses or any outcome whose commit state is unknown.

**Rationale**: Permanently `executing` deterministic validation errors are neither truthful nor
recoverable, but automatically marking all exceptions failed could enable unsafe replay after a
committed effect.

**Alternatives considered**: Revert every error to `proposed`; mark every exception failed;
automatically retry; allow rejection of indeterminate execution.

## Decision 18: Derive public unions from typed operation contracts

**Decision**: Publish each cost operation and shipment-purpose combination as a complete
machine-readable branch derived from runtime request types, with capability guidance for fields
whose cross-field meaning cannot be expressed structurally.

**Rationale**: A schema that is locally rich but empty after live wrapper conversion is not a
public contract. Derivation plus deployed comparison prevents registry, SDK and docs drift.

**Alternatives considered**: Prose-only documentation; validation-error probing; a separately
maintained JSON schema.
