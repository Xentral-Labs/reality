# Docs Locale Contract

## Routes

- English: `/<relative-path>`
- German: `/de/<relative-path>`
- Dutch: `/nl/<relative-path>`
- Spanish: `/es/<relative-path>`
- Existing unprefixed routes keep their meaning.

## Selector and fallback

Every normal page exposes English, Deutsch, Nederlands, and Español. Selection maps the
current relative path to its locale prefix. A missing counterpart offers the English
canonical route, never a broken destination.

## Content and search

Each translated tree mirrors canonical English Markdown paths. Navigation and search
expose the same areas and guide order. Search controls are localized for the active
locale and index its static content.

## Authority

Translations explain but do not redefine the canonical domain. Code identifiers,
tables in code form, environment variables, routes, formulas, quantities, currencies,
and opaque IDs remain stable.
