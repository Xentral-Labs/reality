# Data model and state contracts

## Existing authorities

No new database table, column, operational status or source/evidence relationship is planned.

- `ChangeProposal` in `db/core.py` remains the action authority: tenant, opaque ID, tool type, actor, status, input/output JSON text, decision user/time.
- `BusinessEvent.action_id` correlates actual effects; immutable event payloads prove past quantities.
- Commitments, their revisions, reservations, movements and corrections determine current operational position.
- Documents/lines/SourceRecords supply provenance through existing shortest true links.
- Existing ChatSession/ChatMessage retain company conversations.

## Typed presentation contracts (not stored authority)

`DeliveryWorkRow`: commitment ID, document/line IDs when present, counterparty/item/location references, unit, effective promised/due values, fulfilled/open/active-reserved decimal strings, blockers and exact filter scope.

`DeliveryCase`: row context, item/location-scoped physical/reserved/available observations, linked records, bounded history with completeness metadata and observation status. A closed commitment is readable by ID even when absent from open work.

`DeliveryActionReview`: version, proposal ID, normalized tool/arguments, original review, business effect, requested/applied/shortage quantities, reference labels, state fingerprint, review token and provenance. Decimal values remain strings; labels do not become identity.

## Review storage in existing proposal JSON

A versioned reserved `_delivery_review` envelope lives in immutable proposal input, beside business arguments. It contains scope/request identity, the exact normalized intended action, review-time facts and their revision fingerprint/token. Strip the envelope before handler calls and reject user-supplied reserved metadata. It is historical approval/audit evidence, never a current-stock authority.

Proposal output retains legacy top-level receipt fields and additive `_delivery_result` verification metadata. The input preserves the original review after output changes. Old unversioned inputs remain readable and obtain a bound review before new confirmation. Edits reject/invalidate the old proposed authority and create a new reviewed proposal; do not overwrite a decision's historical intent.

## Lifecycle

Editable local draft has no ChangeProposal until prepare. Existing states remain `proposed`, `executing`, `executed`, `rejected`; stale/invalid review and observation-unavailable are response/presentation conditions, not invented business statuses. A known pre-execution validation failure must leave a non-executed reviewable outcome. A handler exception after the execution boundary remains conservatively unresolved until evidence settles it.

Normal confirmation claims once, records effects with the proposal's action ID and returns a receipt. Replay returns the same receipt. Recovery reads evidence and may settle an already recorded execution under the shared lock; it never invokes the business handler again.

## Company Chat context

Preserve existing messages. New case-context annotations are persisted in versioned message content and rendered as a context label plus readable question. Only server-validated context informs tools. Untrusted message text cannot forge authorization or a valid reviewed action.

## Scope and validation

Every read, mutation, lock, request identity and related-reference lookup is company/actor-scoped. All IDs are opaque. Positive exact quantities, current holds, tracking identities and fulfillment/stock rules are validated by shared services. Mixed units/locations are never silently aggregated. Practice rules remain unchanged.

## Migration and rollback

No Alembic migration is planned. Versioned JSON parsing is additive; old records stay readable. Deploy service/token handling before exposing new clients; rollback disables new-shell entry but retains reviewed-proposal endpoints and token-aware legacy handlers until new proposals settle. Do not downgrade services to a version that can execute a reviewed proposal without its guard. Any later proven schema need requires a separately reviewed amendment.
