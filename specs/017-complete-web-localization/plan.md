# Implementation Plan: Complete Web Localization

**Branch**: `[017-complete-web-localization]` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Close the accepted `016/FR-013` gap by making the existing localization catalog the
single auditable inventory for English, German, Dutch, and Spanish. Replace the
German-only, fixed-file audit with deterministic discovery of in-scope frontend source
and strict per-language validation. Complete the translated catalogs, preserve English
runtime fallback and protected invariant/original content, then collect four-language
build, automated, and visual evidence before changing the baseline status.

The design keeps the existing lightweight localization boundary. It adds no runtime
dependency, backend behavior, database field, or alternate business path.

## Technical Context

**Language/Version**: TypeScript 5.8, ECMAScript 2022, Node.js 22
**Primary Dependencies**: React 19, Vite 7, TypeScript compiler API already used by the audit
**Storage**: Source-controlled localization catalogs only; no PostgreSQL or browser-storage change
**Testing**: Deterministic Node audit tests, strict catalog audit, TypeScript/Vite build, representative desktop/mobile visual review
**Project Type**: Independent React frontend with repository-level GitHub quality gates
**Constraints**: English canonical source/fallback; `en`, `de`, `nl`, `es` advertised; language independent of locale/timezone; lossless source/business content; no new dependency unless proven necessary
**Scale/Scope**: Current product-owned text under `frontend/src`; four languages; public, auth, product, settings, state, and accessibility copy

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Localization changes product-owned UI copy only; raw Source, Evidence, documents, IDs, and Reality values remain untouched and tested. | PASS |
| Reality owns operational state | Catalogs translate labels only; no operational or financial state is introduced or stored. | PASS |
| Proven schema only | No database, migration, typed business field, or persistence change. | PASS |
| Tenant + shared service boundaries | No request, authority, repository, or application-service path changes; existing preferences remain authoritative. | PASS |
| Spec/test traceability | Every FR/DR maps to catalog, audit, fallback, preference, visual, or baseline-evidence proof below and later to explicit tasks. | PASS |
| Explainable web behavior | Stable domain terms, opaque IDs, original evidence, and trace links remain unchanged while surrounding interface copy is translated. | PASS |
| Smallest coherent design | Reuse the current catalog and compiler-based audit; reject a framework migration and backend translation service as unnecessary. | PASS |

Post-design re-evaluation: PASS. The catalog/audit contract, logical data model, and
validation guide introduce no exception to the Constitution.

## Repository Structure and Layer Changes

```text
frontend/
├── package.json                         # strict audit/test commands
├── scripts/
│   ├── i18n-audit.mjs                  # discover source and validate every language
│   └── i18n-audit.test.mjs             # audit behavior regressions
└── src/
    ├── Auth.tsx                        # localized public authentication boundary
    ├── LandingPage.tsx                 # language selection and auth-link continuity
    ├── landing.css                     # responsive language popover
    ├── localization-core.ts            # deterministic public-language resolution
    └── localization.tsx                # complete catalogs, fallback, explicit invariants

.github/workflows/quality.yml            # run strict localization evidence
docs/SPEC_COVERAGE_MATRIX.md              # close gap only after evidence is green
specs/016-web-product/spec.md             # update FR-013 evidence after acceptance
specs/017-complete-web-localization/      # spec, design, tasks, acceptance evidence
```

**Files/layers affected**: Presentation localization and repository quality automation
only. `frontend/src/localization.tsx` remains the shared runtime boundary; public
authentication joins that boundary and preserves the landing-page language through
`frontend/src/Auth.tsx`, `LandingPage.tsx`, and `localization-core.ts`. The audit consumes
frontend sources and the catalog without calling backend services. No backend, domain,
tool, API, model, migration, or generated `frontend/dist` file is planned.

## Design

### Reality flow

Source → Evidence → Reality is not transformed. Product-owned labels around those
records may be translated, while raw payloads, business content, opaque IDs, approved
invariant domain terms, and shortest true links retain their original values.

### Service and adapter flow

The existing user preference selects a language at the presentation boundary. The
localization module resolves canonical English source text against the selected catalog
and falls back to English when runtime lookup is unexpectedly absent. Number, date,
money, quantity, and timezone formatting continue through their independent preference
path.

At verification time, the audit discovers in-scope frontend source files, extracts
static user-facing candidates and catalog entries, applies a narrow explicit invariant
registry, and emits one result per language. Any missing, blank, invalid, or undiscovered
coverage causes the strict command to fail. CI invokes it after the frontend build.

### Data and migration impact

No persisted entity or migration is added. The logical objects in `data-model.md` are
source-controlled runtime/build-time structures only. Rollback needs no data reversal.

### Failure, security, and tenant behavior

- Runtime lookup failure returns canonical English rather than an internal key or blank.
- Strict audit failure identifies the affected language and source text and exits nonzero.
- Dynamic/user/upstream values are excluded by explicit boundary rules, not translated.
- Existing tenant/account preference authorization is unchanged.
- Catalog text is inert presentation data and never authority.
- No mutation, confirmation, idempotency, or cross-tenant semantics are introduced.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-005 | audit unit/integration | `frontend/scripts/i18n-audit.test.mjs`: discovers all in-scope source files and a newly added fixture string | Current audit scans only `App.tsx` and `Auth.tsx`. |
| FR-002–FR-004 | audit unit/integration | Per-language completeness rejects missing and blank de/nl/es entries | Current audit combines entries and describes German only. |
| FR-006 | audit unit | Explicit invariants pass; unapproved fallback/equal-English entries fail | Current ignored-pattern heuristic can hide strings without a recorded reason. |
| FR-007 | localization unit | Unknown lookup returns canonical English and never blank/internal-key output | Existing fallback lacks focused executable proof. |
| FR-008, DR-001–DR-004 | localization unit/story | Source payload, Evidence text, user content, IDs, and trace samples remain unchanged | No focused four-language lossless-boundary proof exists. |
| FR-009 | localization unit/story | Changing language does not change locale or timezone preferences | Existing behavior is not proven by this feature's acceptance test. |
| FR-010 | visual acceptance | Four-language desktop/mobile matrix for representative public, auth, operational, configuration, loading, empty, error, and confirmation states | Dutch/Spanish representative evidence is incomplete. |
| FR-011 | CI integration | Standard audit command is strict and CI fails on a missing entry | Current command succeeds unless manually passed `--strict`. |
| FR-012 | documentation acceptance | `016/FR-013` and coverage matrix change only after preceding evidence passes | Baseline currently records a Documented gap. |
| SC-001–SC-008 | final acceptance | Build, audit tests, strict audit, visual matrix, diff/spec review | Current per-language evidence is incomplete. |

Tests are added or changed before catalog completion and observed failing where practical.
The implementation PR records initial failure and final passing commands.

## Rollout and Rollback

Roll out as one frontend/catalog quality change. Runtime fallback remains compatible
during development; the strict gate prevents release until complete. No deployment
ordering or migration is required.

Rollback reverts catalog, audit, tests, workflow, and evidence together. Translation
quality defects should be corrected in the affected entry without weakening the audit.
Reverting the feature requires restoring `016/FR-013` to Documented gap.

## Review Risks

- Extraction may miss a source pattern or classify dynamic business content as UI copy.
- Identical English wording may require contextual translation.
- Catalogs may be complete but editorially weak.
- Longer translations may clip controls or reduce mobile usability.
- Broad exemptions could hide real debt.
- Updating `016/FR-013` before all evidence passes would overstate the baseline.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
