# Feature Specification: Complete Web Localization

**Feature Branch**: `[017-complete-web-localization]`
**Created**: 2026-08-31
**Status**: Approved
**Language**: English
**Input**: "Complete and audit the advertised English, German, Dutch, and Spanish web localization so that 016/FR-013 can move from Documented gap to Verified as-is."

## Context and Intent

### Problem

The web product advertises English, German, Dutch, and Spanish, but current proof does
not establish complete user-facing text coverage for every language. The existing audit
is German-oriented, currently reports 28 uncatalogued English strings, and does not
measure Dutch or Spanish completeness. Users can therefore select an advertised
language and still encounter avoidable English fallback without a failing quality gate.

This weakens product consistency and leaves `016/FR-013` as a documented gap. The first
post-baseline change should close that bounded gap and prove that the new specification
workflow works end to end.

### Scope

- Establish one measurable inventory of static user-facing web text.
- Complete German, Dutch, and Spanish translations for that inventory.
- Audit English, German, Dutch, and Spanish independently and fail when required
  coverage is incomplete.
- Preserve safe English fallback for unexpected or newly introduced text while making
  missing advertised-language coverage visible to development and review.
- Verify representative public, authentication, operational, configuration, loading,
  empty, error, and confirmation states in every advertised language.
- Update the Web Product baseline evidence for `016/FR-013` only after all acceptance
  evidence passes.

### Non-Goals

- Translating user-entered content, external source payloads, Evidence, document
  contents, business identifiers, or raw diagnostic data.
- Translating stable domain terms whose cross-surface identity must remain consistent,
  including SourceRecord, Evidence, Reality, Commitment, Reservation, and Movement.
- Adding languages beyond English, German, Dutch, and Spanish.
- Changing business rules, tenant authority, persistence, domain state, or the
  independent locale and timezone preferences.
- Rewriting product copy, redesigning pages, or completing unrelated Web UX gaps.

### Existing Contracts

- [`specs/016-web-product/spec.md`](../016-web-product/spec.md), especially FR-013,
  FR-014, SC-005, and SC-006.
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md), especially Accounts and access, Public
  product page, and shared Web acceptance rules.
- [`docs/SPEC_COVERAGE_MATRIX.md`](../../docs/SPEC_COVERAGE_MATRIX.md), documented gap
  `016/FR-013`.
- [`AGENTS.md`](../../AGENTS.md) and the project Constitution.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Work in a Complete Selected Language (Priority: P1)

As a user, I can select English, German, Dutch, or Spanish and use the web product
without avoidable untranslated interface text interrupting the experience.

**Why this priority**: A language advertised in account preferences is a product promise,
not a partial preview.

**Independent Test**: Select each supported language and traverse representative public,
authentication, operational, data, settings, loading, empty, error, and confirmation
states; every inventoried interface string is presented in the selected language or is
an explicitly approved invariant term.

**Acceptance Scenarios**:

1. **Given** a user selects German, Dutch, or Spanish, **When** they navigate all audited
   representative states, **Then** every inventoried static interface string is rendered
   from the selected language catalog.
2. **Given** English is selected or no preference exists, **When** the same states are
   opened, **Then** complete English interface text is shown.
3. **Given** the interface displays a stable domain term, opaque ID, or original business
   content, **When** the surrounding UI is translated, **Then** that protected value
   remains unchanged and distinguishable from interface copy.

---

### User Story 2 - Detect Translation Gaps Before Release (Priority: P1)

As a reviewer, I can see a separate, deterministic completeness result for every
advertised language so missing coverage cannot pass unnoticed.

**Why this priority**: Catalog completeness cannot remain a manual claim that drifts as
new interface text is added.

**Independent Test**: Run the localization audit against the unchanged product and
observe a passing result for all four languages; remove one required translation and
observe a failing result that names the language and missing text.

**Acceptance Scenarios**:

1. **Given** all required catalogs are complete, **When** the localization audit runs,
   **Then** it reports English, German, Dutch, and Spanish separately with zero missing
   required strings and succeeds.
2. **Given** any required catalog entry is missing, **When** the audit runs, **Then** it
   fails and identifies the affected language and missing text.
3. **Given** a new user-facing static string is added, **When** no corresponding catalog
   coverage or approved exemption exists, **Then** the audit fails before the change can
   satisfy the release gate.

---

### User Story 3 - Fall Back Safely Without Hiding Debt (Priority: P2)

As a user, I receive understandable English text instead of a blank or broken control
when an unexpected translation lookup cannot be resolved.

**Why this priority**: Runtime safety remains necessary even when completeness is
enforced before release.

**Independent Test**: Request an unknown translation key in each non-English language;
the user sees the English source text, while the completeness audit still rejects an
unapproved missing catalog entry when it belongs to the audited inventory.

**Acceptance Scenarios**:

1. **Given** a runtime translation is unexpectedly unavailable, **When** the text is
   rendered, **Then** readable English fallback appears and the surrounding page remains
   usable.
2. **Given** fallback was used for text in the required inventory, **When** the audit
   runs, **Then** the missing selected-language entry is reported rather than counted as
   complete coverage.

---

### User Story 4 - Close the Approved Baseline Gap with Evidence (Priority: P2)

As a product owner, I can trace the completed localization work back to the previously
approved Web Product gap and see objective evidence for closing it.

**Why this priority**: Baseline status must change because executable proof improved,
not merely because implementation changed.

**Independent Test**: Review `016/FR-013` after all feature checks pass and confirm its
status points to per-language audit and representative-state evidence with no remaining
language-specific completeness gap.

**Acceptance Scenarios**:

1. **Given** all requirements and acceptance evidence in this feature pass, **When** the
   Web Product baseline is reviewed, **Then** `016/FR-013` changes from `Documented gap`
   to `Verified as-is` and cites the new proof.
2. **Given** any advertised language remains incomplete, **When** baseline evidence is
   reviewed, **Then** `016/FR-013` remains a documented gap.

### Edge Cases

- Duplicate English source text appears in several components or contexts.
- The same English word requires different translations in different contexts.
- Text contains interpolation values, plural-sensitive quantities, punctuation,
  Unicode characters, or accessibility-only labels.
- A value resembles interface copy but is actually user-entered or upstream content.
- A catalog entry exists but is empty, whitespace-only, or identical to English without
  being an approved invariant term.
- A language preference is unavailable, malformed, or changes while the app is open.
- A newly added frontend source file contains user-facing text but is not audited.
- English fallback makes the page usable while still representing incomplete coverage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST maintain a deterministic inventory of static user-facing
  web text across all product-owned public, authentication, and application surfaces.
- **FR-002**: Every inventoried string MUST have complete English, German, Dutch, and
  Spanish presentation, except for explicitly approved invariant terms.
- **FR-003**: The completeness audit MUST evaluate and report each advertised language
  independently.
- **FR-004**: The completeness audit MUST fail when an inventoried string is missing,
  empty, or otherwise lacks acceptable coverage in any advertised language.
- **FR-005**: The audit MUST detect newly introduced user-facing text across all in-scope
  web source surfaces rather than relying on a permanently fixed subset of pages.
- **FR-006**: Approved invariant terms MUST be explicit, narrowly justified, and applied
  consistently across languages; fallback alone MUST NOT count as an exemption.
- **FR-007**: Missing runtime translations MUST fall back to readable English without
  blank labels, broken controls, or exposure of an internal translation key.
- **FR-008**: User-entered values, immutable source payloads, Evidence/document content,
  opaque IDs, and raw diagnostic values MUST remain lossless and MUST NOT be translated.
- **FR-009**: Language choice MUST remain independent from number/date locale and display
  timezone, preserving existing preference behavior.
- **FR-010**: Representative visual review MUST cover all four languages across public,
  authentication, operational, configuration, loading, empty, error, and confirmation
  states, including desktop and mobile layouts affected by longer translations.
- **FR-011**: The release gate MUST run the strict per-language completeness audit and
  reject changes that introduce unapproved missing coverage.
- **FR-012**: `016/FR-013` MUST remain a documented gap until FR-001 through FR-011 and
  their acceptance evidence pass; only then may its evidence status become Verified as-is.

### Domain and Traceability Requirements

- **DR-001**: Localization MUST remain presentation-only and MUST NOT alter Source →
  Evidence → Reality records, relationships, calculations, or trace paths.
- **DR-002**: Opaque IDs and shortest true links MUST remain unchanged; translated labels
  MUST NOT become identifiers or authoritative state.
- **DR-003**: Language selection and audit behavior MUST preserve tenant and account
  boundaries and MUST NOT create a second business-service path.
- **DR-004**: Original external and business content MUST remain lossless and clearly
  distinguishable from product-owned interface translations.

### Key Entities *(when data is involved)*

- **Advertised Language**: One of English, German, Dutch, or Spanish available to users.
- **Interface String**: Product-owned static text shown to a user, including visible copy,
  control labels, placeholders, status text, and accessibility labels.
- **Translation Entry**: The language-specific presentation of one interface string.
- **Invariant Term**: An explicitly approved term or value that remains unchanged across
  languages because translating it would harm identity, traceability, or domain clarity.
- **Completeness Result**: Per-language evidence listing covered, missing, invalid, and
  exempt interface strings and the resulting pass/fail outcome.

## Success Criteria *(mandatory)*

- **SC-001**: The strict audit reports zero missing or invalid required entries for each
  of English, German, Dutch, and Spanish.
- **SC-002**: Adding one untranslated in-scope string causes the release gate to fail and
  identify all affected languages in a single audit run.
- **SC-003**: In representative review, 100% of audited public, authentication,
  operational, configuration, loading, empty, error, and confirmation states display
  the selected language except for approved invariant or original business content.
- **SC-004**: A missing runtime lookup produces readable English in every tested language
  with zero blank labels, exposed internal keys, or unusable controls.
- **SC-005**: Desktop and mobile review finds zero clipped critical actions, inaccessible
  labels, or unusable navigation caused by German, Dutch, or Spanish text length.
- **SC-006**: Original Source, Evidence, document, user-entered, ID, and diagnostic sample
  values remain byte-for-byte or semantically unchanged in localization tests.
- **SC-007**: `016/FR-013` is backed by executable per-language proof and is no longer
  listed as a language-coverage gap after owner review.
- **SC-008**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- English is the canonical source and runtime fallback language.
- English, German, Dutch, and Spanish remain the complete advertised language set for
  this feature.
- The recorded count of 28 uncatalogued German-source strings is starting-state evidence;
  the required outcome is zero across the complete current inventory, not a fixed count.
- Existing account language, locale, and timezone preferences remain authoritative.
- Native or fluent editorial review is desirable but not required to prove catalog
  completeness; language-quality corrections can be reviewed separately if they do not
  change coverage behavior.
- Closing `016/FR-013` depends on passing the full frontend build, localization audit,
  affected-state visual review, and final owner review.
- The product owner approved this specification on 2026-08-31.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-005 | US2 scenarios 1 and 3 | Inventory discovery and new-source regression tests |
| FR-002–FR-004, FR-006 | US1 scenario 1; US2 scenarios 1–3 | Per-language completeness and exemption tests |
| FR-007 | US3 scenarios 1–2 | Runtime fallback and strict-audit regression tests |
| FR-008–FR-009 | US1 scenarios 2–3 | Original-content and preference-independence tests |
| FR-010–FR-011 | US1 scenario 1; US2 scenarios 1–3 | Four-language state matrix, build, and release gate |
| FR-012 | US4 scenarios 1–2 | Baseline evidence review and coverage-matrix update |
| DR-001–DR-004 | US1 scenario 3; US3 scenario 1 | Traceability, identity, tenant, and lossless-content review |
| SC-001–SC-008 | All stories | Final acceptance report linked from tasks and PR |
