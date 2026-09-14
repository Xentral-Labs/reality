# Research: Demo Entrypoint Equivalence

## Decision 1: Compare the compact guided demo

**Decision**: `docs/DEMO_SPEC.md` and `ensure_demo` define the scenario. The September
2026 normal-month scenario remains separate.

**Rationale**: `015/FR-010` names interactive CLI, auto mode, and Web onboarding. Both
CLI demo modes already call `ensure_demo`; normal month is a different command.

**Alternatives considered**: Compare normal month across interfaces. Rejected as scope
expansion that would not prove the documented guided-demo gap.

## Decision 2: Reuse the existing shared operation

**Decision**: Keep `ensure_demo(session, tenant)` as the canonical operation unless tests
expose a defect. Add no second orchestration service.

**Rationale**: It already composes normal tenant-scoped reference, Movement, source
ingestion, Evidence, Commitment, Reservation, and Chat services.

**Alternatives considered**: Copy the scenario into Web or add a generic scenario engine.
Rejected as duplicate business logic or unnecessary abstraction.

## Decision 3: Make Web demo creation explicit and opt-in

**Decision**: Extend authenticated company creation with an optional demo choice. Omitted
or false means empty company; true is sent only after a distinct Web confirmation.

**Rationale**: Current Web onboarding creates only an empty tenant. An optional input
preserves compatibility and reuses ownership setup.

**Alternatives considered**: Seed every new company or reproduce each CRUD step in the
browser. Rejected because the first surprises users and the second moves business logic
into Web.

## Decision 4: Compare categorized authoritative manifests

**Decision**: Build a test-only manifest from fresh tenant-scoped reads with reference,
source, evidence, reality, derived, and explanation sections.

**Rationale**: Stored and derived business state proves equivalence; categories make
failures actionable.

**Alternatives considered**: Screenshots/output strings or counts alone. Rejected because
formatting is not truth and counts miss value and relationship drift.

## Decision 5: Normalize only nondeterministic noise

**Decision**: Alias opaque IDs by unique demo roles and normalize timestamps, ordering,
and run-relative dates. Preserve values, payload semantics, multiplicity, links,
lifecycle, ownership, and derived outcomes.

**Rationale**: Separate tenants generate different IDs while the demo uses dates relative
to UTC today. Narrow normalization avoids both false mismatches and hidden drift.

**Alternatives considered**: Fixed production IDs/dates or ignoring all identifiers and
dates. Rejected as identity misuse or over-normalization.

## Decision 6: Prove real Web wiring without browser automation

**Decision**: Combine authenticated HTTP/PostgreSQL execution with a focused structural
contract over the actual Web onboarding handler and API client.

**Rationale**: Backend execution proves state; the source contract proves the actual Web
action, confirmation, and request without a new browser-test dependency.

**Alternatives considered**: Calling the service directly and labeling it Web, or adding
a full browser stack. Rejected as insufficient or disproportionate.

## Decision 7: Preserve truthful partial-failure behavior

**Decision**: Cancellation creates nothing. After confirmed company creation, population
failure is reported and the possibly partial tenant remains available for explicit
operator handling; safe retry is not claimed and no implicit deletion occurs.

**Rationale**: Existing services commit through normal boundaries. Silent tenant deletion
would be destructive and broader than this feature.

**Alternatives considered**: Automatic deletion or transactional redesign of all demo
services. Rejected as unsafe or materially broader.
