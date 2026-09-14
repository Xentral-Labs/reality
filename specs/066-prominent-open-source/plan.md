# Implementation Plan: Prominent Open-Source Entry

**Branch**: `[066-prominent-open-source]` | **Date**: 2026-09-04 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Retain the shared Site header's configured Docs utility link and remove the redundant open-source paragraph after the landing page's closing account CTA. Product Web's Docs resource and the recognizable ERP marks on the Docs home page remain unchanged.

## Technical Context

**Language/Version**: TypeScript 5.8, React 19, CSS
**Primary Dependencies**: Vite 7, lucide-react, existing Site localization provider
**Storage**: None
**Testing**: Node contract tests, i18n audit, TypeScript/Vite production build, browser visual review
**Project Type**: Independent static public Site
**Constraints**: No API, authentication state, tenant state, live GitHub data, new route, or new colour literal
**Scale/Scope**: One shared navigation link and removal of one landing-page paragraph across responsive states

## Constitution Check _(blocking gate)_

| Principle                          | Evidence in this plan                                                                    | Result |
| ---------------------------------- | ---------------------------------------------------------------------------------------- | ------ |
| Source → Evidence → Reality        | Presentation-only static links and copy; no business records or interpretation           | PASS   |
| Reality owns operational state     | No document or operational state is introduced                                           | PASS   |
| Proven schema only                 | No schema or persistence change                                                          | PASS   |
| Tenant + shared service boundaries | Public Site remains tenant-independent and calls no service                              | PASS   |
| Spec/test traceability             | FR/DR mappings below lead to failing contracts, i18n audit, build, and visual proof      | PASS   |
| Explainable web behavior           | The section links to source and public documentation; no operational answer is created   | PASS   |
| Smallest coherent design           | One persistent discovery point plus one explanatory section; no page or live integration | PASS   |

Post-design check: all rows remain PASS. Planning may proceed.

## Repository Structure and Layer Changes

```text
provider-site/src/components/PublicHeader.tsx       # shared repository discovery link
provider-site/src/LandingPage.tsx                   # open-source section and destinations
provider-site/src/landing.css                       # token-based responsive presentation
provider-site/src/localization.tsx                  # German, Dutch, Spanish catalog entries
provider-site/scripts/site-contract.test.mjs        # executable navigation/section contract
apps/web/src/App.tsx                            # documentation resource root destination
apps/web/scripts/product-boundary.test.mjs      # configured Docs root contract
apps/docs/content/index.md                      # ERP marks on English home page
apps/docs/content/de/index.md                   # ERP marks on German home page
apps/docs/.vitepress/theme/custom.css           # responsive brand-row presentation
apps/docs/scripts/docs-contract.test.mjs        # home-page marks contract
specs/066-prominent-open-source/                # intent, plan, tasks, review evidence
```

**Files/layers affected**: Public presentation only. No domain, service, tool, API, data, or deployment changes.

## Design

### Reality flow

N/A. The feature publishes static project-discovery links and does not create or interpret Source, Evidence, or Reality records.

### Service and adapter flow

N/A. The static Site renders the canonical repository URL and configured Docs URL without requesting either destination.

### Data and migration impact

None. Rollback is a source-only revert of markup, styles, catalog entries, and tests.

### Failure, security, and tenant behavior

The Site remains useful if GitHub is unavailable because no live data is fetched. Destinations have descriptive labels. No tenant, session, secret, mutation, or confirmation boundary is involved.

## Test Strategy and Traceability

| Requirement            | Test level             | Planned test                                                            | Expected initial failure         |
| ---------------------- | ---------------------- | ----------------------------------------------------------------------- | -------------------------------- |
| FR-001, FR-002, DR-003 | Site contract          | Shared header has canonical repository link and existing actions remain | Link is absent                   |
| FR-003-FR-005          | Site contract          | Landing section order, claims, repository and Docs actions              | Section is absent                |
| FR-006                 | Localization           | Existing i18n audit covers every new source string                      | New strings lack translations    |
| FR-007                 | Build + visual         | Production build and desktop/mobile keyboard review                     | New surface is absent            |
| FR-008, DR-001-DR-002  | Static contract + diff | No fetch/API/state and presentation-only paths                          | Boundary contract precedes code  |
| DR-004                 | Content review         | Copy contains only inspectable repository truths                        | Review guards unsupported claims |

## Rollout and Rollback

Ship with the existing static Site artifact. No ordered deployment or migration is required. Roll back the feature changes if navigation density or section hierarchy regresses.

## Review Risks

- The fourth header item could crowd account and language actions at intermediate widths.
- New copy could overstate project maturity rather than invite inspection.
- A new visual band could lose hierarchy in dark mode or compete with the final account CTA.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
| ---------------------- | ---------- | ---------------------------- | -------- |
| None                   | —          | —                            | —        |
