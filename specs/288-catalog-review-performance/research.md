# Research: Shared Runtime Catalog

## Decision 1: Extend the existing runtime catalog boundary

**Decision**: Use `reality.catalogs` as the sole owner of the validated process-local snapshot and
add bounded section reads there.

**Rationale**: The codebase already starts the API by validating `runtime_application_catalog()`,
has explicit reset support, returns isolated copies, and tests successful reuse and failed-build
retry. Extending that boundary is smaller and more coherent than introducing another cache.

**Alternatives considered**:

- Cache inside Proposal Review: rejected because MCP, CLI and other services would still rebuild.
- Cache in API/Web/MCP adapters: rejected because it forks behavior by transport and violates the
  shared-service boundary.
- External distributed cache: rejected because metadata is deployment-local, small and immutable
  for the process lifetime; infrastructure would add invalidation and availability risk.

## Decision 2: Keep raw construction explicit and uncached

**Decision**: Preserve `load_application_catalog()` as the fresh builder. Runtime code uses the
validated snapshot; validation, generation and tests may deliberately call the builder.

**Rationale**: Tests must detect source-file drift and generators must observe current checkout
content. Making the raw builder itself cached would make those workflows order-dependent and
could hide invalid catalog changes.

**Alternatives considered**:

- Decorate the raw builder directly: rejected because it conflates fresh validation with runtime
  reuse and makes invalidation implicit.
- Replace every call mechanically: rejected because not every caller has runtime semantics.

## Decision 3: Return copied sections to narrow consumers

**Decision**: Add a central accessor that returns a deep copy of one validated top-level section.
Retain the existing full-copy accessor for callers that publish the complete application reference.

**Rationale**: Copy isolation prevents accidental global mutation. Copying one section avoids the
cost of duplicating all catalog sections for Proposal Review, fact validation or capability help.

**Alternatives considered**:

- Return the shared dictionary directly: rejected because any caller could corrupt global runtime
  metadata.
- Deep-copy the full catalog everywhere: correct but unnecessarily expensive for narrow reads.
- Convert the nested catalog into immutable proxy types: rejected as a wider compatibility change
  across serialization, tooling and tests.

## Decision 4: Make first initialization single-publication and retryable

**Decision**: Guard snapshot creation and publication with one process-local synchronization
boundary. Publish only after successful validation/enrichment; failures leave the snapshot empty.

**Rationale**: Standard memoization may invoke the wrapped function more than once for concurrent
misses. A single-publication boundary satisfies the one-build target and ensures no partial object
is observable. Leaving failure uncached preserves the existing retry contract.

**Alternatives considered**:

- Rely only on API lifespan warm-up: rejected because MCP, CLI, workers and direct services can
  initialize independently.
- Accept duplicate concurrent builds: safe for content but violates the measured efficiency goal.
- Cache exceptions: rejected because corrected deployment/test state could not recover in-process.

## Decision 5: Inventory production raw-builder callers

**Decision**: Migrate the five eligible runtime consumers identified during planning and retain
only the canonical snapshot initializer as a production raw-build call.

**Rationale**: A source assertion prevents later services from silently bypassing the shared
boundary. Current eligible consumers are catalog code inspection, fact contract validation,
storyline catalog indexing, capability description and proposal next-step guidance.

**Alternatives considered**:

- Fix Proposal Review only: rejected because it leaves the architectural duplication that the
  clarified scope explicitly addresses.
- Ban the raw builder repository-wide: rejected because tests and generators require fresh builds.

## Decision 6: Separate correctness tests from the performance acceptance benchmark

**Decision**: Keep deterministic build-count/content/retry assertions in pytest and provide a
repeatable local service benchmark for the 200 ms p95 target.

**Rationale**: Wall-clock thresholds in a shared CI runner are noisy. Build counts prove the cache
contract deterministically; the documented benchmark proves the user-facing target in the local
PostgreSQL environment where the regression was observed.

**Alternatives considered**:

- Hard wall-clock assertion in every unit-test run: rejected as flaky and environment-sensitive.
- Manual timing only: rejected because it is not repeatable or reviewable.
