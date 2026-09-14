# Feature Specification: Multilingual Product Documentation

**Feature Branch**: `[050-docs-localization]`

**Created**: 2026-09-03

**Status**: Complete

**Language**: English

**Input**: User description: "Make the product documentation available in all product languages: English, German, Dutch, and Spanish."

## Context and Intent

### Problem

Reality's product interface supports English, German, Dutch, and Spanish, but the
product documentation is available only in English. Readers who select another
product language cannot learn the domain model, follow operational guides, or use the
reference material in the same language. The newly expanded Business Reality guide is
especially difficult to use when a reader must translate ERP terminology mentally.

### Scope

Provide the complete public documentation journey in English, German, Dutch, and
Spanish. Readers can choose a language from every page, navigate and search within
that language, retain the equivalent page when switching where possible, and receive
the English page as a clearly defined fallback when a translation is unavailable.

### Non-Goals

- Translating repository-internal specifications, plans, ADRs, source code, or
  developer comments.
- Translating lossless external payload examples whose original language is
  intentionally preserved.
- Automatically publishing unreviewed machine translation as authoritative content.
- Adding product-interface languages beyond English, German, Dutch, and Spanish.
- Creating different business behavior or domain rules per language.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the complete documentation in a product language (Priority: P1)

As a German-, Dutch-, or Spanish-speaking ERP practitioner, I can open the Docs in my
language and follow the complete reader journey without being redirected through
English-only navigation.

**Why this priority**: Complete localized content is the direct user value. A language
selector without translated guidance does not solve the comprehension problem.

**Independent Test**: Select each supported language and visit every documented reader
area and every Business Reality book chapter; each page, navigation label, and local
search interface is presented in the selected language.

**Acceptance Scenarios**:

1. **Given** a reader is on the English documentation home page, **When** the reader
   selects German, **Then** the German home page opens with German navigation and
   links to the complete German reader journey.
2. **Given** a reader opens the Dutch or Spanish Business Reality guide, **When** the
   reader follows every chapter link, **Then** every chapter is available in that
   language and preserves the same business meaning and worked quantities as English.
3. **Given** a reader uses local documentation search, **When** the selected language
   is German, Dutch, or Spanish, **Then** results from that language are discoverable
   with localized search controls.

---

### User Story 2 - Switch language without losing context (Priority: P2)

As a reader comparing terminology, I can change language from a documentation page and
remain on the equivalent topic whenever that translation exists.

**Why this priority**: Context-preserving switching makes multilingual documentation
usable for readers and reviewers who compare domain terms across languages.

**Independent Test**: Open representative pages at matching paths in all four
languages and switch among them; the corresponding topic opens rather than always
returning to a generic landing page.

**Acceptance Scenarios**:

1. **Given** a reader is viewing the German Reservations chapter, **When** Spanish is
   selected, **Then** the Spanish equivalent of that chapter opens.
2. **Given** an equivalent translated page is unavailable, **When** the reader follows
   the language path or a content link, **Then** the English equivalent is available as
   the fallback rather than a broken page.
3. **Given** any supported localized page, **When** the reader views the language
   selector, **Then** English, German, Dutch, and Spanish are all identifiable in their
   own language.

---

### User Story 3 - Maintain translation parity safely (Priority: P3)

As a documentation maintainer, I can detect missing pages, broken localized links,
missing navigation entries, and materially incomplete book translations before the
Docs are published.

**Why this priority**: Multilingual documentation becomes misleading if one locale
silently falls behind or points to another language without an intentional fallback.

**Independent Test**: Remove or rename a localized page or required guide section in a
test fixture and verify that the documentation quality gate fails with the affected
locale and path.

**Acceptance Scenarios**:

1. **Given** the English documentation inventory, **When** a supported locale lacks a
   required counterpart, **Then** the documentation quality gate reports the missing
   locale and page.
2. **Given** a localized relative link targets no page, **When** quality checks run,
   **Then** publication is blocked with the broken source and target.
3. **Given** translated terminology, **When** source identifiers, code values, formulas,
   and opaque example IDs are compared, **Then** their technical meaning remains
   consistent across languages.

### Edge Cases

- A reader opens an unprefixed legacy English URL bookmarked before localization.
- A localized page exists but its equivalent chapter has been added only in English.
- A language switch occurs from a nested book chapter or a not-found page.
- Search terms contain accents, umlauts, punctuation, or untranslated technical
  identifiers such as `SourceRecord` and `SettlementAllocation`.
- A translated paragraph contains Markdown links, tables, code blocks, formulas, or
  admonitions that must retain their structure.
- Browser language differs from a language explicitly selected in the documentation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The public documentation MUST support English, German, Dutch, and Spanish
  as explicit reader-selectable languages.
- **FR-002**: Every required public documentation page in the English reader journey
  MUST have a corresponding page in German, Dutch, and Spanish at release.
- **FR-003**: Each language MUST present localized top navigation, sidebar labels,
  page-outline labels, search controls, not-found recovery, and footer copy.
- **FR-004**: A reader MUST be able to switch language from every normal documentation
  page.
- **FR-005**: Language switching MUST retain the equivalent page path when that page
  exists.
- **FR-006**: Unprefixed existing documentation URLs MUST remain valid as the canonical
  English experience.
- **FR-007**: English MUST be the explicit fallback when a localized counterpart is
  unavailable; fallback behavior MUST not produce a broken link.
- **FR-008**: Local documentation search MUST index and return content for the selected
  language and present localized controls.
- **FR-009**: Translations MUST preserve domain identifiers, record type names when used
  as code vocabulary, formulas, quantities, currencies, opaque IDs, code samples, and
  Source → Evidence → Reality semantics.
- **FR-010**: Translations MUST use stable, understandable ERP terminology for their
  language and MUST not introduce language-specific business rules.
- **FR-011**: Every Business Reality guide chapter and its overview MUST be available
  in all four languages with matching chapter order and cross-navigation.
- **FR-012**: Documentation quality checks MUST verify locale inventory parity,
  localized navigation coverage, relative-link validity, and required guide-section
  coverage before publication.
- **FR-013**: Documentation maintainers MUST be able to identify the exact locale and
  page when a parity or link check fails.
- **FR-014**: Explicit reader language selection MUST take precedence over browser
  language detection.
- **FR-015**: The documentation MUST not claim that a translation changes or overrides
  the authoritative English specifications and domain contracts.

### Key Entities

- **Documentation locale**: One supported language, its human label, path prefix,
  localized interface copy, navigation, and fallback relationship.
- **Localized page**: A translated counterpart preserving one canonical page's topic,
  structure, technical identifiers, examples, and links.
- **Canonical page inventory**: The complete set of English public pages that each
  release locale must cover.
- **Translation parity result**: A quality-check outcome identifying missing or
  structurally incomplete locale content.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the public English page inventory has German, Dutch, and Spanish
  counterparts at release.
- **SC-002**: A reader can switch among all four languages from any representative
  normal page in no more than two interactions and remain on the equivalent topic.
- **SC-003**: All four localized reader journeys complete without broken internal links
  or missing navigation destinations.
- **SC-004**: Search finds a known language-specific phrase from every major reader area
  in its corresponding language.
- **SC-005**: Automated quality checks identify 100% of deliberately removed localized
  pages and required guide chapters in the maintained test cases.
- **SC-006**: A terminology review finds no changed quantities, currencies, formulas,
  record identities, or Source → Evidence → Reality relationships across the four
  Business Reality guide versions.

## Assumptions and Dependencies

- The supported documentation languages intentionally match the existing product
  languages: English (`en`), German (`de`), Dutch (`nl`), and Spanish (`es`).
- English remains the canonical authoring language and the unprefixed default locale.
- The first release translates the complete current public documentation inventory,
  not only the Business Reality guide.
- Existing public URLs must remain stable; translated languages may use locale-prefixed
  paths.
- Translation is editorial content and may be assisted mechanically, but it is checked
  for domain meaning, structural parity, and technical-token preservation before
  release.
- The existing public Docs deployment, local search, responsive design, and external
  application/site links remain available.

## Open Questions

None. The user confirmed that the required languages are English, German, Dutch, and
Spanish, and explicitly approved machine-assisted translation of the public Docs
Markdown.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
| --- | --- | --- |
| FR-001–FR-003, FR-008 | US1 scenarios 1–3 | Locale configuration, inventory, navigation, search-copy, link, and production-build checks |
| FR-004–FR-007, FR-014 | US2 scenarios 1–3 | Native locale routing, canonical English-path checks, complete counterpart inventory, and not-found recovery |
| FR-009–FR-011, FR-015 | US1 scenario 2; US3 scenario 3 | Guide parity, protected vocabulary, native-language markers, and chapter cross-link checks |
| FR-012–FR-013 | US3 scenarios 1–2 | Contract tests report the exact missing locale, page, or relative-link target |
| SC-001–SC-006 | All scenarios | Quickstart acceptance review, 18 Docs contract tests, VitePress production build, and diff review |
