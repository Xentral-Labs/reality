# Implementation Plan: First-Time Fact Rule Wizard

**Date**: 2026-09-12 | **Spec**: [spec.md](spec.md)

## Summary

Add a presentation-only five-stage wizard for new and never-activated rules. Reuse
existing evidence, editor, result components and application endpoints. Keep the
completed-rule workbench intact. Scope accepted by the owner before planning.

## Technical Context

TypeScript, React 19 and existing Vite/Tailwind toolchain. PostgreSQL and existing
Python services remain authoritative and unchanged. No new dependencies. Tests use
existing Node contracts, browser fixture infrastructure and the complete pytest suite.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Existing evidence selection retains exact opaque source, subject and rule links | PASS |
| Reality owns operational state | No document state or business derivation added | PASS |
| Proven schema only | No schema change | PASS |
| Tenant + shared service boundaries | Existing tenant API, component keyed by tenant, stale callback guards | PASS |
| Spec/test traceability | Owner approval; tasks map all FR/DR to test-first proofs | PASS |
| Explainable web behavior | Source links, sentence preview, actual simulation and explicit milestones | PASS |
| Received values not recomputed | Evidence value preserved; preview only describes selections | PASS |
| Smallest coherent design | Reuse components; no new engine, queue, API or persisted wizard | PASS |

Pre-design and post-design checks pass. No constitutional exceptions.

## Repository Structure and Layer Changes

Domain → services → tools reviewed: no changes required. Adapter changes:
- `apps/web/src/unified/FactRuleWizard.tsx`: guided state, review and submission.
- `apps/web/src/unified/ruleWizardState.ts`: presentation milestone helpers and starter metadata.
- `apps/web/src/unified/RulesWorkbench.tsx`: route new/incomplete setup to wizard.
- `apps/web/src/unified/RuleDraftEditor.tsx`: optional wizard guidance without changing existing editor defaults.
- `apps/web/src/unified/RuleEvidence.tsx`: optional guided copy and context for evidence actions.
- `apps/web/src/localization.tsx`: en keys and de/nl/es copy.
- `apps/web/scripts/fact-rule-wizard.test.mjs`, `fact-rule-wizard-browser.mjs`: new proofs.
- `apps/web/scripts/guided-rules-browser.mjs`: adapt setup assertions while retaining legacy operations coverage.
- `docs/WEB_SPEC.md`: durable wizard contract.

## Design

Use existing create, evidence, recommend, decide, prepare, simulate and activate calls.
Each write has its own review and explicit confirmation; navigation never executes a
write. A saved question enters evidence; accepted Fact enters configuration; saved
draft enters testing; a successful read-only simulation enables activation review.
Resume a draft-only question at testing, with no remembered simulation. Active or
previously disabled versions use the existing workbench. Derive stage availability
from loaded evidence and accepted destination; keep selected stage as ephemeral UI state.

The wizard owns its detail returned from writes, input state, review snapshot and
simulation for one mounted tenant/question. Parent refreshes register after writes.
Editing invalidates simulation immediately. Save normalizes through validateDraft and
hydrates from the returned immutable version. Back never saves an unchanged version.
Unknown writes lock further changes pending reload; failed reads allow retry. Pending
writes block close. Unmount guards prevent delayed reads/writes from updating another
context. Close states explain which milestone persists and that unsaved changes are lost.

## Data and Migration Impact

None. Existing RealityGap, entries, SourceRecord, InterpretationRule and Fact only.
No persisted wizard state, new opaque IDs, or business relationships.

## Test Strategy and Traceability

| Requirements | Planned proof | Initial failure |
|---|---|---|
| FR-001–003 | Entry/starter/navigation/validation browser test | New rule has only two fields |
| FR-004, DR-001 | Evidence selection, false/zero, empty/error/non-Fact fixture paths | No guided evidence stage |
| FR-005, FR-011 | Existing draft unit + legacy browser regression | New guidance missing; existing baseline retained |
| FR-006–008 | Save/test/revise/activate/resume/exit browser journey; milestone unit tests | No version-aware stage navigation |
| FR-009, DR-002 | Read-only, stale async, tenant reset, uncertain write browser cases | New state guards absent |
| FR-010 | i18n audit, all languages, desktop/390px keyboard screenshots | New wizard absent |

Required gates: `make spec-check`, `make lint`, `make test`, `make site-build`,
`make web-build`, web contract tests, i18n audit, focused new and existing browser
suites, `make docs-catalog-check`, `git diff --check`. Backend suite includes migration
checks. Catalog generation is unnecessary because no executable catalog changes.

## Rollout and Rollback

Build the web app normally. Revert adapter changes to restore previous UI; no data
migration or rollback required. Keep valid questions and immutable draft versions.
No external deployment or business mutation is part of this coding task.

## Review Risks

Stale simulation, late responses after context changes, accidentally repeated draft
creation, inaccessible footer on mobile, starter examples implying unsupported mappings.
