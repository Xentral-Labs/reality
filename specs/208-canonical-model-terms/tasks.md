# Tasks: Canonical Reality model terms

## Specification and design
- [x] T001 Review approved scope in spec.md and Constitution Check in plan.md.
- [x] T002 Analyze spec.md, plan.md and tasks.md before implementation.

## User Story 1 - Shared model vocabulary
- [x] T003 [US1] [FR-001] [FR-002] Add failing catalog checks in apps/web/scripts/model-terminology.test.mjs.
- [x] T004 [US1] [FR-001] [FR-002] Update model and related labels in apps/web/src/localization.tsx and invariant labels in apps/web/scripts/i18n-invariants.mjs.

## User Story 2 - Localized operation
- [x] T005 [US2] [FR-003] Test preservation of business/control copy in apps/web/scripts/model-terminology.test.mjs and existing localization-contract.test.mjs.
- [x] T006 [US2] [FR-003] Preserve English keys and localization boundaries; document naming policy in docs/WEB_SPEC.md.

## Verification and review
- [x] T007 Run frontend contracts, i18n audit, build, formatting and spec-check; record evidence in verification.md.
- [x] T008 Review final diff against FR-001–003 and existing workspace edits.

## Dependencies and implementation strategy
T001 → T002 → T003/T005 → T004/T006 → T007 → T008. Tests precede edits. One catalog change delivers the coherent vocabulary. Validation commands may run independently; no parallel implementation is needed.

## Requirement Coverage
| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T003 | T004 |
| FR-002 | T003 | T004 |
| FR-003 | T005 | T006 |
