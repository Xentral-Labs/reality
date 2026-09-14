# Research: Master Data Adapter Parity

## Matrix boundary

**Decision**: Cover Party, Item, and Location create, update, deactivate, and reactivate
across CLI, JSON API, and Product Web: 36 cells.

**Rationale**: This is the shared lifecycle surface explicitly named by the baseline,
master-data contract, CLI, API, and current Web register.

**Alternatives considered**: PaymentTerm and pricing have different surfaces and focused
proofs; including them would expand rather than close `004/FR-016`.

## Comparison vocabulary

**Decision**: Reload authoritative state and compare family-specific canonical
snapshots. Generated identities use stable test aliases.

**Rationale**: Business fields, relationships, source meaning, tenant ownership, and
lifecycle must match; Rich text, HTTP envelopes, UI labels, IDs, and timestamps need not.

**Alternatives considered**: Output comparison creates false failures; database dumps
compare noise; mocks do not prove persistence.

## Product Web evidence

**Decision**: Pair an executable structural Node contract over the actual Master Data
handler source, API-client calls, request mappings, and error rendering with real
HTTP/PostgreSQL parity tests.

**Rationale**: Web intentionally has no independent server mutation layer. This proves
the operator action honestly without adding browser infrastructure solely for parity.

**Alternatives considered**: A direct service call or unused helper labeled Web and
duplicated React business logic violate the spec. A new browser-test dependency is
unnecessary because stored behavior belongs to the tested HTTP boundary; the structural
contract must fail when the used handler wiring drifts.

## Placement

**Decision**: Keep matrix declarations, invokers, aliases, and snapshots in tests.

**Rationale**: They are proof metadata, not runtime business state.

**Alternatives considered**: A persisted capability registry or production parity
service adds architecture solely for testing.

## Production changes

**Decision**: Change production code only after a failing parity case demonstrates drift.

**Rationale**: The gap is missing focused proof, not an already-known feature defect.

**Alternatives considered**: Replacing entity services with generic CRUD would discard
useful domain validation and increase risk.

## Failure and tenancy proof

**Decision**: Compare both tenants before/after invalid and foreign operations,
including roles, sources, events, Evidence, and Reality.

**Rationale**: Similar error text does not prove atomicity or non-disclosure.

**Alternatives considered**: Exit/status assertions alone are insufficient; identical
wording is only presentation parity.
