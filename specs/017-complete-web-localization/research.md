# Research: Complete Web Localization

## Decision 1: Retain the Existing Localization Boundary

**Decision**: Keep the source-text catalog and localization module, strengthening their
structure and tests only where deterministic four-language coverage requires it.

**Rationale**: Language, locale, timezone, fallback, and translated rendering already
exist. The proven gap is completeness and evidence, not a missing framework.

**Alternatives considered**:

- Third-party internationalization framework: rejected as migration scope without a
  direct completeness benefit.
- Backend/database translations: rejected because no runtime administration use case is proven.
- Duplicated page trees per language: rejected because they would drift.

## Decision 2: One Canonical Inventory, Per-Language Results

**Decision**: Discover product-owned static text from all in-scope frontend source files
and compare it independently with English, German, Dutch, and Spanish coverage.

**Rationale**: One inventory prevents language-specific scope drift; separate results
identify the exact gap for every advertised language.

**Alternatives considered**:

- German-only audit: cannot prove Dutch or Spanish.
- Aggregate pass/fail count: obscures the affected language.
- Fixed component filename list: lets new files silently escape coverage.

## Decision 3: Strict Completeness Is the Default Gate

**Decision**: The standard audit exits nonzero for missing, blank, or invalid required
coverage. Diagnostic-only behavior, if retained, uses a separate command.

**Rationale**: An optional strict flag allowed visible gaps while CI remained green.

**Alternatives considered**:

- Warnings only: do not prevent regression.
- Enforce only after merge: detects defects too late.
- Manual count review: nondeterministic.

## Decision 4: Narrow Explicit Invariant Registry

**Decision**: Text intentionally identical across languages is explicitly listed with a
reason. Pattern ignores are limited to clear non-copy values.

**Rationale**: Stable domain terms and opaque identifiers remain unchanged, but broad
heuristics can silently accept untranslated prose.

**Alternatives considered**:

- Accept every English-equal value: hides omissions.
- Translate every token: harms identity and traceability.
- Keep only the broad ignore regex: lacks item-level review evidence.

## Decision 5: Test Audit Behavior with Controlled Fixtures

**Decision**: Audit tests use small controlled source/catalog fixtures for complete,
missing, blank, invariant, dynamic-content, discovery, and multi-language cases.

**Rationale**: Production output proves a current result but not that regressions are
detected. Fixtures provide deterministic failure semantics without browser-test scope.

**Alternatives considered**:

- Snapshot production console output: may remain green when extraction misses a pattern.
- Add browser automation solely for completeness: disproportionate; visual review stays separate.

## Decision 6: Separate Completeness from Editorial Quality

**Decision**: Prove non-empty language-specific coverage and usable layout. Native
editorial review is desirable but not claimed by the automated gate.

**Rationale**: Automation cannot reliably certify linguistic nuance. Separating claims
prevents false assurance while closing the objective coverage gap.

**Alternatives considered**:

- Automated semantic-correctness claim: unverifiable.
- Block until certified translation review: a different scope and approval requirement.
