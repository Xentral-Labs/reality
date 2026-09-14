# Localization Audit Contract

## Input

The audit consumes all in-scope product frontend source discovered under the configured
root, its canonical English interface inventory, German/Dutch/Spanish catalog entries,
and explicit approved invariants. Generated bundles, dependencies, tests, external
fixtures, and user/business data are outside discovery.

## Classification

Inventory includes product-owned visible copy, labels, placeholders, helper/action text,
loading/empty/error/status/confirmation messages, accessibility text, and supported
interpolated templates.

It excludes opaque IDs, routes, machine keys, codes, numeric literals, user/upstream
content, Source/Evidence/document/diagnostic values, and explicit reviewed invariants.
An exclusion heuristic may not exempt ordinary prose merely by spelling or punctuation.

## Output

One stable audit run emits one result per language containing language code, discovered,
covered, invariant, missing and invalid counts, details with source locations, and final
status. Exit is successful only when all four languages pass.

## Runtime Fallback

- Canonical English is returned for unresolved non-English lookup.
- Missing lookup never renders blank or exposes an internal key.
- Runtime fallback does not satisfy inventory completeness.
- Original business/source content bypasses translation unchanged.

## Required Regressions

1. Complete four-language fixtures pass.
2. One missing entry fails and names its language/source.
3. Missing entries in several languages appear in one run.
4. Blank entries fail.
5. Approved invariants pass; unapproved English-equal entries fail.
6. A new source file below the in-scope root is discovered.
7. Excluded business/dynamic values do not become translation requirements.
8. Output ordering is deterministic.
