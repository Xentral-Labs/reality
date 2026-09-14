# Design Model: Multilingual Documentation

No database model changes. These static entities define publication behavior.

## DocumentationLocale

- Unique key: `root`, `de`, `nl`, or `es`.
- Language tag, native label, path prefix, localized metadata and theme copy.
- English root fallback for every translated locale.

## CanonicalPage

- Unique relative English Markdown path and reader area.
- Required structural/semantic markers.
- Exactly one counterpart for each translated locale.

## LocalizedPage

- Locale and canonical relative path.
- Natural-language title/body with protected technical tokens.
- Locale-local internal links, canonical external links, and intentional fallback links.

## Validation rules

- Every canonical page has one German, Dutch, and Spanish counterpart at the same path.
- Every relative link resolves.
- Every locale has the guide overview and eight numbered chapters.
- Record names, formulas, quantities, currencies, IDs, environment variables, and code
  examples retain technical meaning.
- Explicit selection determines locale; browser preference does not override it.

## Lifecycle

```text
English page added/changed -> translations updated -> parity, links, format and build
verified -> all locales published atomically
```

A missing counterpart is a failed release gate, not a normal published state.
