# Implementation Plan: Multilingual Product Documentation

**Branch**: `[050-docs-localization]` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

**Language**: English for repository artifacts; public reader content also uses German, Dutch, and Spanish.

## Summary

Use native documentation locales. Keep unprefixed English routes canonical, add
structurally identical `de/`, `nl/`, and `es/` trees, localize theme navigation and
search, and enforce page, link, navigation, and guide parity in Docs contract tests.

## Technical Context

**Language/Version**: TypeScript configuration, ECMAScript tests, Markdown content
**Primary Dependencies**: VitePress 1.6.4 built-in i18n and local search
**Storage**: Static repository content; no runtime persistence
**Testing**: Node test runner, Prettier, VitePress build, repository spec policy
**Project Type**: Independently deployed static documentation site
**Constraints**: English URLs stable; technical identifiers retain exact spelling
**Scale/Scope**: Four locales and the complete current public Markdown inventory

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Every translation preserves the canonical model and identifiers; no domain writes. | PASS |
| Reality owns operational state | Presentation only; no document-owned status language is added. | PASS |
| Proven schema only | No database, typed field, migration, or stored-state change. | PASS |
| Tenant + shared service boundaries | Static Docs has no tenant or application access. | PASS |
| Spec/test traceability | FR-001–FR-015 map to locale, link, content, build, and review checks. | PASS |
| Explainable web behavior | Every locale retains the guide, formulas, Inspector, and trace vocabulary. | PASS |
| Smallest coherent design | Native locale routing reuses the static site, local search, and deployment. | PASS |

All Constitution gates pass without exception.

## Repository Structure and Layer Changes

```text
apps/docs/.vitepress/config.mts                  # shared/per-locale configuration
apps/docs/content/                               # canonical unprefixed English
apps/docs/content/{de,nl,es}/                    # translated counterparts
apps/docs/scripts/docs-contract.test.mjs         # locale and parity contracts
specs/050-docs-localization/                     # delivery artifacts
```

**Files/layers affected**: Static Docs configuration, Markdown, and Docs tests only.
No domain, service, API, product Web, database, or deployment change.

## Design

### Reality flow

No business records change. Translations preserve Source → Evidence → Reality,
identifiers, directions, formulas, quantities, corrections, and shortest true links.

### Service and adapter flow

VitePress resolves root as English and prefixed directories as German, Dutch, and
Spanish. Native locale routing retains relative paths. Per-locale theme configuration
supplies navigation, sidebar, outline, search, footer, edit, and recovery text. Static
output continues through the existing Docs build and hosting adapter.

### Data and migration impact

No schema or application data change. Locale directories are additive. Rollback removes
them and their configuration while retaining former English URLs.

### Failure, security, and tenant behavior

Inventory tests catch missing pages before build; link failures identify locale and
path. English is canonical fallback. No credentials, tenant records, or authenticated
services are exposed.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-003, FR-004, FR-014 | Docs contract | Four locales, native labels, localized UI, selector routing | Config has no locales |
| FR-002, FR-011, FR-013 | Docs contract | Compare page inventory and eight chapters per locale | Locale trees absent |
| FR-005–FR-007 | Build/contract | Path symmetry, stable English, fallback-safe routing | Locale routes absent |
| FR-008 | Contract/build | Locale search controls and marker phrases | Search is English-only |
| FR-009, FR-010, FR-015 | Content/review | Protected tokens and semantic comparison | Translations absent |
| FR-012 | Docs contract | Missing-page, link, navigation, chapter gates | Checks are single-locale |

## Rollout and Rollback

Publish all locale trees and configuration in one static artifact. Existing English
links, variables, container, and health route remain unchanged. Rollback removes only
the additive locale content and config.

## Review Risks

- Fluent translation may subtly alter Commitment, Reservation, Movement, or settlement meaning.
- Locale trees can drift unless parity tests fail by default.
- Root-relative and nested links can diverge.
- Search controls can be localized without correctly scoped content.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
