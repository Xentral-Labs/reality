# Implementation Plan: Canonical Reality model terms

## Technical Context
React/TypeScript frontend with shared dictionaries in apps/web/src/localization.tsx and node:test catalog contracts. Presentation-only change; no dependencies.

## Constitution Check
| Principle | Result | Evidence |
|---|---|---|
| I Source → Evidence → Reality | PASS | Display vocabulary only; original records untouched |
| II Reality authority | PASS | No operational rules changed |
| III Proven schema | PASS | No schema change |
| IV Tenant/service boundaries | PASS | No reads/writes changed |
| V Spec/test evidence | PASS | Approved user scope; regression first; mapped tasks |
| VI Explainable UI | PASS | Names match the model and Inspector |
| VII Simplicity/storage | PASS | Edit existing catalogs; no runtime abstraction |
| VIII Received values | PASS | Original-content boundary unchanged |

## Design
Update existing literal catalog entries in place, including later Object.assign overrides. Avoid runtime text replacement and preserve English sources. Register exact canonical labels in i18n-invariants.mjs. Add catalog-based contracts for every supported non-English language. Related search/navigation labels retain localized verbs. Domain → services → tools need no change; implement only the adapter copy. Update docs/WEB_SPEC.md to supersede translated category naming.

## Validation
First run new regression tests against existing catalogs and observe failure. Then run frontend contract suite, i18n audit, build, changed-file formatting and make spec-check. Existing localization tests cover formatting preferences and original content. No backend/migration/catalog-generation changes, so backend database and generated tool reference gates are not applicable. Review diff for unrelated changes and stable English sources.

## Rollback and Risks
Revert only this feature's catalog/test/contract edits. No migration. Risks: duplicate late overrides, inconsistent related labels, localization audit treating invariant names as untranslated copy. Test effective catalogs and audit.
