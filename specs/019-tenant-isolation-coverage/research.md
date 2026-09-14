# Research: Complete Tenant Isolation Coverage

## Decision 1: Use a Checked-In Family Catalog

**Decision**: Map stable business families to classification, public operations,
evidence, and explicit exemption reasons in one source-controlled catalog.

**Rationale**: Existing proof is distributed and cannot demonstrate exhaustive coverage.
A catalog makes completeness reviewable and machine-checkable without runtime changes.

**Alternatives considered**: Test names alone do not detect new operations; endpoint-by-
endpoint mapping duplicates shared services; a documentation-only matrix cannot fail.

## Decision 2: Discover Callables and Existing Registries

**Decision**: Discover top-level public tenant-aware functions in an explicit service
module set and cross-check registered projections, application tools, canonical catalog
services, and explicit indirect-context operations.

**Rationale**: No current authority covers the entire public business surface. Combined
discovery catches ordinary, dynamic, and indirect boundaries without scanning private
implementation details.

**Alternatives considered**: Package-wide discovery is too broad; command/projection
catalogs alone omit master data, details, integrations, chat, artifacts, and mutations;
decorating every service adds production abstraction solely for evidence.

## Decision 3: Prove Behavior by Family

**Decision**: Group operations only when they share an isolation behavior and scenario
factory, while listing every covered operation explicitly.

**Rationale**: One test per function is repetitive; one test per broad domain can hide
unexercised operations. Explicit membership balances precision and maintainability.

**Alternatives considered**: A universal parameterized test cannot express complex
valid setup and side-effect assertions; incidental happy paths do not prove isolation.

## Decision 4: Build an Asymmetric Two-Tenant Graph

**Decision**: Seed overlapping human values but different Source, Evidence, Reality,
quantity, money, integration, and projection data for two tenants.

**Rationale**: Both tenants must be populated to detect collection/aggregate leakage;
unequal values prevent coincidentally correct totals.

**Alternatives considered**: An empty foreign tenant proves little; separate ad hoc
fixtures would drift in identity overlap and cross-stage consistency.

## Decision 5: Canonical Service Proof, Representative Adapter Proof

**Decision**: Require exhaustive evidence at shared business boundaries and focused
proof that tools and representative API paths propagate tenant context.

**Rationale**: All adapters must share services. Repeating every family through every
transport adds cost without strengthening canonical isolation.

**Alternatives considered**: Adapter-only tests can hide service leaks; exhaustive
transport duplication encourages adapter-specific logic.

## Decision 6: Classify Global Administration Explicitly

**Decision**: Keep global tenant/access operations in the catalog with `global_admin`,
governing authority, reason, and boundary evidence where externally reachable.

**Rationale**: Silent omission makes completeness ambiguous. These operations are
intentionally administrative, not failures of tenant business scoping.

**Alternatives considered**: Omitting functions without `tenant_id` misses indirect
boundaries; forcing tenant scope onto platform administration changes approved policy.

## Decision 7: Correct Only Proven Defects

**Decision**: Add failing isolation proof first, then make the smallest shared-service
correction only where the new suite proves a contract violation.

**Rationale**: The feature closes evidence debt, not speculative refactoring debt.

**Alternatives considered**: Pre-emptive tenant rewrites lack a use case; endpoint-only
patches violate the shared-service boundary.
