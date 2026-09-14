# Tasks: Complete unified business journey
## Gates
- [x] T001 Owner-approved scope reviewed, Constitution PASS, research complete.
- [x] T002 Spec/plan/tasks analysis: seven requirements mapped, no unresolved ambiguity or critical findings.
## Proof before repair
- [x] T003 [US1,US2] [FR-001,FR-002,FR-003,FR-004,DR-001,DR-002] Add packages/reality-core/tests/test_unified_business_journey.py for linked partial/full refund stories and exact data assertions.
- [x] T004 [US1,US2] [FR-001,FR-002,FR-003,FR-004,DR-001,DR-002] Add tests/browser/unified_business_journey.py and apps/web/scripts/unified-business-journey-browser.mjs with isolated real API, ordinary owner login, actual forms and cleanup.
- [x] T005 [US1,US2] [FR-005] Run journey, document reproduced defects in quickstart.md and add focused regressions before repairing applicable existing source paths.
- [x] T005a [FR-002,FR-005] Correct credit/refund reversal balance and introductory wording in apps/web/src/unified/FinancialReversalCard.tsx and localization.tsx; real journey asserts accurate labels.
## Verification
- [x] T006 [FR-001,FR-002,FR-003,FR-004,FR-005,DR-001,DR-002] Complete real-browser/service story and all required regression checks after source freeze; inspect screenshots and evidence.
- [x] T007 Review final changes, isolation/cleanup, provenance and scope; update docs/WEB_SPEC.md, docs/SPEC_COVERAGE_MATRIX.md, docs/V0_CHECKLIST.md and docs/ideas/unified-capability-inventory.md with verified status only.
## Dependencies and coverage
T003/T004 precede T005; T005 precedes final T006/T007. All FR/DR appear in test tasks and harness/repair tasks. Repair paths are limited to existing services/tools/web adapters and unified UI proven by the journey; add specific subtasks for discovered defects.
