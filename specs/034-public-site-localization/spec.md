# Feature Specification: Public Site Localization

**Feature Branch**: `[034-public-site-localization]`
**Created**: 2026-09-02
**Status**: Approved
**Language**: English
**Input**: "The public site header offers English, German, Dutch, and Spanish, but selecting Dutch or Spanish does not change any visible copy. Make the public site completely available in all four advertised languages using the catalog pattern already proven in the product web."

## Context and Intent

### Problem

The public site advertises four languages. Its header language control lists English,
Deutsch, Nederlands, and Español, stores the selection, rewrites the `?lang=` query,
sets the document language attribute, and preserves the selection into product-web
account links. Only English and German copy exists, so a visitor who selects Dutch or
Spanish sees the language code change in the header while every sentence on the page
remains English.

The cause is structural, not a single defect. Public-site copy lives as bilingual
alternatives inside the page components: one `copy` object with `en` and `de` branches
plus roughly 330 inline `language === "de" ? … : …` decisions across the landing,
packages, and education routes. `provider-site/src/localization.tsx` is an empty provider
stub, so the site has no catalog, no translation lookup, and no coverage gate. Every
non-German language therefore silently falls back to English, and no automated check
fails.

This breaks the promise the language control makes, and it leaves the public site behind
the product web, where `017-complete-web-localization` already proves complete English,
German, Dutch, and Spanish coverage through catalogs and an auditing gate.

### Scope

- Make the complete public site — landing, `/platform`, `/why-reality`, and the shared
  public header — readable in English, German, Dutch, and Spanish.
- Establish English as the single source language in public-site components and move
  every translation into per-language catalogs in `provider-site/src/localization.tsx`.
- Preserve the existing German copy exactly as the German catalog while restructuring.
- Add Dutch and Spanish translations for the complete public-site text inventory.
- Audit all four languages and fail the site gate when advertised coverage is missing,
  empty, untranslated, or loses a protected domain term.
- Keep safe English fallback for text that is newly introduced or intentionally
  invariant, while making missing advertised coverage visible in development and review.
- Translate the localized values that are not page text nodes: document titles and
  accessible labels on the public routes.
- Format monetary amounts for the selected language instead of translating them, so
  currency position and decimal separator follow the locale.
- Remove public-site copy that renders nowhere, so the English source stays the truth
  about what a visitor can read.
- Update `022-public-site`, `docs/WEB_SPEC.md`, and the coverage matrix to state the
  four-language public-site contract.

### Non-Goals

- Adding languages beyond English, German, Dutch, and Spanish.
- Rewriting product copy that is actually rendered, redesigning routes, or changing
  layout, styling, navigation structure, pricing, or early-access positioning. Removing
  copy that renders nowhere is in scope; rewording visible copy is not.
- Translating stable domain terms whose cross-surface identity must stay constant,
  including Reality, SourceRecord, Evidence, Fact, Commitment, Reservation, Movement,
  and Ledger Entry.
- Translating brand names, connector names, agent-system names, protocol acronyms,
  business identifiers such as `R-2087` or `COM-C-2087-R2`, code samples, or payload
  examples.
- Translating the language names inside the language control itself.
- Changing the product web's own localization, its catalogs, or its audit tooling.
- Making the public site depend on the product web at build, test, or runtime.
- Adding server-side rendering, a translation service, a runtime translation API, an
  i18n framework dependency, or per-language routes and domains.
- Changing business rules, persistence, tenant authority, or any API, CLI, MCP, or Chat
  behavior. The public site remains a static browser deployment with no application
  dependency.

### Existing Contracts

- [`specs/022-public-site/spec.md`](../022-public-site/spec.md), especially FR-007,
  FR-015, FR-018, and FR-025.
- [`specs/017-complete-web-localization/spec.md`](../017-complete-web-localization/spec.md)
  as the proven catalog, invariant, and audit pattern for the product web.
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md), section "Public product page".
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md), the independent Site deployment.
- [`docs/SPEC_COVERAGE_MATRIX.md`](../../docs/SPEC_COVERAGE_MATRIX.md), the Public Site row.
- [`AGENTS.md`](../../AGENTS.md) and the
  [Business Reality Constitution](../../.specify/memory/constitution.md).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the Whole Public Site in a Selected Language (Priority: P1)

As a visitor who selects Nederlands or Español, I can read the complete public site in
that language, so the advertised language control is truthful.

**Why this priority**: The site currently promises four languages and delivers two.
Every other improvement is secondary to making the visible promise real.

**Independent Test**: Select each of the four languages on the landing, `/platform`,
and `/why-reality` routes and verify that all page copy, including headings, body text,
labels, diagram annotations, list items, accessible labels, and document titles, appears
in the selected language, with no unintended English fallback.

**Acceptance Scenarios**:

1. **Given** the landing route in English, **When** a visitor selects Nederlands,
   **Then** all public-site copy is Dutch, the header shows the Dutch selection, and no
   catalogued sentence remains English.
2. **Given** the same selection, **When** the visitor opens `/platform` or
   `/why-reality`, **Then** those routes render in the selected language, including
   their document titles.
3. **Given** a selected language, **When** copy contains a protected domain term, brand
   name, business identifier, or code sample, **Then** that term appears unchanged.
4. **Given** Español is selected, **When** the visitor reads a sentence containing a
   number, price, or capacity value, **Then** the sentence is Spanish and the numeric
   value is correct and complete.
5. **Given** any advertised language, **When** the visitor reads a standalone monetary
   amount, **Then** it is formatted for that language rather than translated.
6. **Given** any of the four languages, **When** the visitor uses the language control,
   **Then** the language names inside that control remain in their own language.

### User Story 2 - Keep the Selection Across the Public Site and Into the Product (Priority: P1)

As a visitor, my language choice survives navigation inside the public site and follows
me into sign-in and account creation.

**Why this priority**: A complete translation is worthless if one link resets the
visitor to English; the existing `?lang=` and account-link contract must keep holding
for all four languages.

**Independent Test**: Select each language, navigate between all public routes, reload
with the resulting URL, and follow the sign-in and account-creation links.

**Acceptance Scenarios**:

1. **Given** a selected language, **When** the visitor navigates between the landing,
   `/platform`, and `/why-reality` routes, **Then** the selection is preserved in the
   URL and in the rendered language.
2. **Given** a `?lang=` value for any supported language, **When** the route is loaded
   directly, **Then** that language renders without requiring a stored preference.
3. **Given** an unsupported or malformed `?lang=` value, **When** the route is loaded,
   **Then** the site falls back to a supported language without an error state.
4. **Given** a selected language, **When** the visitor opens sign-in or account
   creation, **Then** the product-web destination preserves that language selection.
5. **Given** a stored preference from an earlier visit, **When** the visitor returns
   without a query parameter, **Then** the stored supported language is applied.

### User Story 3 - Prevent Silent Language Regressions (Priority: P2)

As a maintainer, I get a failing gate when public-site text is added or changed without
complete advertised-language coverage.

**Why this priority**: Without an executable gate the site drifts back to partial
coverage exactly as it did after the site was split from the product web.

**Independent Test**: Add an untranslated public-site string, empty one catalog value,
copy an English value verbatim into a catalog, and remove a protected domain term from a
translation; each case must fail the site gate with the affected language and string
identified.

**Acceptance Scenarios**:

1. **Given** new English public-site copy without catalog entries, **When** the site
   gate runs, **Then** it fails and names the missing language and source string.
2. **Given** a catalog value that is empty, whitespace, or identical to its English
   source without being declared invariant, **When** the gate runs, **Then** it fails
   for that language and string.
3. **Given** a translation that drops a protected domain term present in the source,
   **When** the gate runs, **Then** it fails for that language and string.
4. **Given** a translated public site with complete coverage, **When** the gate runs,
   **Then** it passes and reports covered, invariant, missing, and invalid counts per
   language.
5. **Given** a German sentence that already existed before this feature, **When** the
   gate runs after restructuring, **Then** that German wording is still delivered
   unchanged.

### Edge Cases

- A language is selected while the page is already rendered, so previously rendered text
  must change without a reload.
- Copy is rendered inside SVG diagram labels and pseudo-tabular annotations rather than
  ordinary paragraphs.
- A sentence embeds a runtime value such as the configured cloud price or early-access
  capacity, so word order differs by language.
- A capacity value of zero switches the sentence to waitlist wording in every language.
- One English string appears in more than one place and must translate consistently.
- An English string is intentionally identical in a target language, such as a brand,
  acronym, or accepted loanword, and must not be reported as missing.
- Code samples, payload examples, and business identifiers appear inside otherwise
  translatable sections.
- A visitor's stored preference contains an unsupported value from an earlier visit.
- The site build must keep working with no product-web dependency installed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The public site MUST render its complete user-facing text in English,
  German, Dutch, and Spanish across the landing, `/platform`, and `/why-reality` routes
  and the shared public header.
- **FR-002**: English MUST be the single source language in public-site components. A
  component MUST NOT contain a language conditional or a per-language copy branch.
- **FR-003**: German, Dutch, and Spanish text MUST live in per-language catalogs keyed by
  the English source string in `provider-site/src/localization.tsx`.
- **FR-004**: Selecting a language MUST apply it to already-rendered and subsequently
  rendered public-site text without requiring a page reload.
- **FR-005**: Localized text that is not a page text node MUST also be translated,
  specifically the public-route document titles and the accessible labels on public
  content.
- **FR-006**: The existing German public-site wording MUST be preserved exactly through
  the restructuring; this feature MUST NOT reword German copy.
- **FR-007**: Text with no catalog entry for the selected language MUST fall back to its
  English source rather than rendering an empty, partial, or error state.
- **FR-008**: A sentence containing a runtime value such as a price or capacity MUST
  render as one grammatical sentence in every language with the runtime value in the
  position that language requires.
- **FR-009**: Protected domain terms, brand and agent-system names, protocol acronyms,
  business identifiers, code samples, and payload examples MUST remain unchanged in all
  languages.
- **FR-010**: The language names inside the language control MUST remain in their own
  language in every selection.
- **FR-011**: An executable audit MUST inventory the public site's user-facing English
  text, compare it against the German, Dutch, and Spanish catalogs, and report covered,
  invariant, missing, and invalid counts per language.
- **FR-012**: The audit MUST fail when a required translation is missing, empty,
  identical to its English source without an explicit invariant declaration, or loses a
  protected domain term present in the source.
- **FR-013**: Strings that are legitimately identical across languages MUST be
  declarable as invariant with a stated reason and MUST be reported as invariant rather
  than missing.
- **FR-014**: The audit MUST run as part of the public-site test and build gate and MUST
  NOT require the product web's dependencies, tooling, or installation.
- **FR-015**: Language selection MUST continue to be resolved from the `?lang=` query
  parameter, then the stored preference, then English, and an unsupported value MUST fall
  back safely.
- **FR-016**: The selected language MUST be preserved across public-route navigation, in
  the route URL, in the document language attribute, and in product-web account links.
- **FR-017**: The public site MUST remain an independent static browser deployment with
  no API, authentication, tenant, product-web, or database dependency.
- **FR-019**: Standalone monetary amounts MUST be formatted for the selected language
  through locale-aware number formatting, MUST NOT be catalogued as translatable strings,
  and MUST be excluded from text translation so a formatted amount is never rewritten.
- **FR-020**: Public-site copy that no route renders MUST be removed rather than
  translated, so the discovered inventory describes only text a visitor can read.
- **FR-018**: The four-language public-site contract MUST be recorded in
  `specs/022-public-site/spec.md`, `docs/WEB_SPEC.md`, and
  `docs/SPEC_COVERAGE_MATRIX.md`, replacing the bilingual statement.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality does not apply. The public site is
  presentation-only, receives no source payload, and creates no Evidence or Reality
  record. It MUST NOT introduce a second description of business rules.
- **DR-002**: Domain vocabulary used in public copy MUST stay identical to the product
  and documentation vocabulary in every language, so a visitor reads the same terms an
  operator sees in the product.
- **DR-003**: No tenant-scoped data, authenticated state, or shared application service
  is involved. The site MUST NOT gain any such dependency to deliver translations.
- **DR-004**: No business table, column, migration, or persisted record is added or
  changed. The stored language preference remains a browser-local presentation value.

### Key Entities *(when data is involved)*

- **Supported language**: One of English, German, Dutch, or Spanish, selectable in the
  public header and expressible as a `?lang=` value.
- **Public-site text inventory**: The set of English user-facing strings discovered in
  public-site components; the measurable basis for coverage.
- **Language catalog**: A mapping from an English source string to its translation for
  one non-English supported language.
- **Invariant string**: A source string declared to stay identical in a target language,
  with a stated reason.

## Success Criteria *(mandatory)*

- **SC-001**: The audit reports 100% coverage of the discovered public-site text
  inventory for German, Dutch, and Spanish, with zero missing and zero invalid entries.
- **SC-002**: Representative review of the landing, `/platform`, and `/why-reality`
  routes in all four languages finds zero unintended English fallback.
- **SC-003**: Every German sentence delivered before this feature is still delivered
  verbatim after it.
- **SC-004**: Public-site components contain zero language conditionals and zero
  per-language copy branches.
- **SC-005**: Each injected regression — missing entry, empty value, English duplicate,
  and dropped domain term — fails the site gate and identifies the affected language and
  string.
- **SC-006**: Language selection, `?lang=` resolution, unsupported-value fallback, and
  account-link language preservation pass for all four languages.
- **SC-007**: The public site test and build gate passes with only the public site's own
  dependencies installed.
- **SC-008**: Every FR and DR maps to an acceptance scenario and an executable proof or
  an explicit, reviewed reason why automation is inappropriate.
- **SC-009**: Every advertised language renders monetary amounts in its own convention,
  the German rendering is unchanged, and zero bare amounts remain in the catalogs.

## Assumptions and Dependencies

- The four advertised languages are exactly those the product web already supports;
  this feature adds no language and removes none.
- The existing German copy is approved product copy and is the reference for tone and
  terminology when writing Dutch and Spanish.
- The product web's catalog, invariant, and audit approach is proven by
  `017-complete-web-localization` and is the pattern to follow, but its tooling is not
  importable because the public site installs, tests, and builds independently.
- Locale and timezone formatting on the public site stays as it is; the site renders no
  tenant data and no localized business numbers beyond static copy values.
- Dutch and Spanish copy is produced by this feature against the approved German
  reference. Automated coverage, invariant declarations, and the protected-term rule are
  the evidence for all four languages; editorial native-speaker certification remains
  outside this feature's claim, as it does for `017-complete-web-localization`.

## Open Questions

No unresolved product-scope questions remain. The product owner decided that the public
site becomes fully four-language using the catalog pattern rather than reducing the
language control to English and German.

## Approval

The product owner approved this specification on 2026-09-02, including the decision to
translate the complete public site into Dutch and Spanish and to keep the four-language
language control.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-004 | US1 scenarios 1–2 | Four-language render proof per public route and live language switch |
| FR-002, FR-003 | US1 scenario 1; US3 scenario 5 | Source-structure contract test plus extracted-catalog German parity |
| FR-005 | US1 scenario 2 | Document-title and accessible-label translation test |
| FR-006 | US3 scenario 5 | Verbatim German wording regression over pre-existing sentences |
| FR-007, FR-013 | US1 scenario 3; US3 scenario 4 | Fallback and invariant-declaration audit cases |
| FR-008 | US1 scenario 4; edge cases | Runtime-value sentence proof for price and capacity, including zero capacity |
| FR-009 | US1 scenario 3 | Protected-term, identifier, and code-sample preservation test |
| FR-010 | US1 scenario 6 | Language-control invariance test |
| FR-011, FR-012 | US3 scenarios 1–4 | Audit inventory, per-language report, and four injected-regression proofs |
| FR-014, FR-017 | US3 scenario 4; edge cases | Site-only gate execution and independence contract test |
| FR-015, FR-016 | US2 scenarios 1–5 | Language-resolution, navigation, and account-link tests for all four languages |
| FR-019, SC-009 | US1 scenario 5 | Locale money-format proof, original-content marking, and bare-amount catalog guard |
| FR-020 | Edge cases; scope boundary | Inventory covers rendered copy only; removed keys reviewed in the diff |
| FR-018 | Final review | Contract and coverage-matrix update review |
| DR-001–DR-004 | US1–US3 | Constitution review, absent-dependency contract test, and zero-schema diff gate |
| SC-001–SC-008 | All stories | Audit report, representative review record, and full site gate |
