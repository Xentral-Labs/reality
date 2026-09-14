# Logical Data Model: Complete Web Localization

This feature adds no persisted business data. These are source-controlled runtime/build-
time structures and audit results only.

## AdvertisedLanguage

| Attribute | Meaning | Validation |
|---|---|---|
| code | Stable language code | Exactly one of `en`, `de`, `nl`, `es` |
| name | Human-readable name | Non-empty |
| isCanonical | Source/fallback marker | Exactly one canonical language (`en`) |

## InterfaceString

| Attribute | Meaning | Validation |
|---|---|---|
| key/source | Stable identity or canonical English text | Non-empty and deterministic |
| locations | Source locations using the text | At least one discovered location |
| kind | Visible text, label, placeholder, status, accessibility text, or supported template | Known audited kind |
| context | Optional disambiguation for identical English wording | Required where meanings differ |

## TranslationEntry

| Attribute | Meaning | Validation |
|---|---|---|
| interfaceString | Translated interface identity | Present in the discovered inventory |
| language | Target advertised language | One entry per required language |
| value | Language-specific presentation | Non-empty and not whitespace-only |
| sourceEquivalent | Intentional equality with English | Allowed only with an approved invariant |

Each InterfaceString has one valid presentation per advertised language. English may use
its canonical source rather than a duplicated catalog record, but is reported explicitly.

## InvariantTerm

| Attribute | Meaning | Validation |
|---|---|---|
| source | Exact protected term/value | Narrow, non-empty, reviewed |
| reason | Identity, brand, domain stability, opaque ID, or original-content boundary | Explicit and non-generic |
| scope | Locations/category where preservation is valid | Cannot exempt ordinary prose broadly |

## CompletenessResult

| Attribute | Meaning | Validation |
|---|---|---|
| language | Audited language | One result for each advertised language |
| discovered | Total interface strings | Shared inventory basis |
| covered | Valid translated/canonical entries | Non-negative |
| invariant | Approved unchanged entries | Non-negative |
| missing | Required entries absent | Zero to pass |
| invalid | Empty/unacceptable entries | Zero to pass |
| details | Language, source, and locations per failure | Required for every failure |
| status | Pass or fail | Pass only when missing and invalid are zero |

## Boundaries and State

- User/upstream values, Evidence/document content, IDs, and raw diagnostics are not
  InterfaceStrings and never enter the catalog.
- A new InterfaceString makes non-canonical language results fail until covered or
  explicitly invariant.
- Runtime English fallback does not change build-time completeness.
- None of these objects is tenant-owned business data or persisted in PostgreSQL.
