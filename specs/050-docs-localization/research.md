# Research: Multilingual Product Documentation

## Native locale routing

**Decision**: Use VitePress built-in `locales`, English at `root`, and `de`, `nl`, `es` directories.

**Rationale**: Native i18n provides locale discovery and per-locale theme configuration
while preserving root URLs. Official guidance recommends parallel locale directories.

**Alternatives considered**: Runtime machine translation is unreviewed and failure-prone;
separate sites duplicate deployment; `/en/` would break existing URLs.

## Switching and fallback

**Decision**: Use route symmetry for context-preserving switching and English root as fallback.

**Rationale**: Full inventory parity keeps readers on-topic; root remains compatible.

**Alternatives considered**: Always returning to a locale home loses context; automatic
browser redirects can override explicit choice.

## Multilingual search

**Decision**: Retain built-in local search with locale-specific interface translations.

**Rationale**: VitePress supports locale-specific local-search configuration without a
new service, credential, dependency, or privacy surface.

**Alternatives considered**: Hosted search has no proven operational need.

## Translation quality

**Decision**: English is canonical; translations use natural prose while preserving code
vocabulary. Tests protect structure and tokens; editorial review protects meaning.

**Rationale**: Linguistic and ERP accuracy cannot be established by file parity alone.

**Alternatives considered**: Literal translation reads poorly; translated class/table
names break traceability.

## Maintainability

**Decision**: Generate locale navigation from shared paths and localized label dictionaries.

**Rationale**: One topology prevents sidebar drift while retaining native labels.

**Alternatives considered**: Four handwritten navigation trees make omissions likely.
