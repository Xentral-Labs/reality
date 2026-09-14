# Data Model: Public Site Localization

## Persistence decision

No persisted entity, field, relationship, constraint, index, or migration is added or
changed. The public site is a static browser deployment with no database, API, tenant, or
authenticated state. Source → Evidence → Reality does not apply to this feature.

## Browser-local state

| Value | Location | Meaning | Change in this feature |
|---|---|---|---|
| `reality.language` | `localStorage` | Last selected public-site language | None. Key, values, and semantics stay as they are. |
| `?lang=` | Route URL | Explicit language request, highest precedence | None. Resolution order stays query → stored → English. |
| `document.documentElement.lang` | DOM | Rendered document language | None. Continues to reflect the selection. |

## Presentation-only structures

| Structure | Shape | Meaning |
|---|---|---|
| Supported language | `"en" \| "de" \| "nl" \| "es"` | The four advertised public-site languages. Unchanged set. |
| Language catalog | `Record<string, string>` per non-English language | English source string → translation. Keys are the English text as written in the components. |
| Numeric-placeholder key | English source with digit runs replaced by `{0}`, `{1}`, … | Lets one sentence carry a runtime price or capacity while each language places the value itself. |
| Invariant declaration | source string → reason | Strings that legitimately stay identical in a target language: domain terms, brands, acronyms, business identifiers, accepted loanwords. |
| Text inventory | set of English source strings with file/line locations | Audit basis for coverage; derived from the components, never stored. |

## Domain vocabulary rule

Reality, SourceRecord, Evidence, Fact, Commitment, Reservation, Movement, and Ledger Entry
keep identical spelling in all four languages, matching the product web and the
documentation. A translation that drops such a term from a sentence that contains it is
invalid and fails the audit.
