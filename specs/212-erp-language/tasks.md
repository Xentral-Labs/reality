# Tasks

## Review gate
- [x] T001 [FR-003] Review scope, spec208 constraints and callers; record decisions in specs/212-erp-language/research.md and plan.md.

## US1: Recognize labels
- [x] T002 [US1] [FR-001] [FR-002] Review de/nl/es and record before/after labels in specs/212-erp-language/research.md; update the existing heading regression in packages/reality-core/tests/test_operational_previews.py and observe red.
- [x] T003 [US1] [FR-001] [FR-002] Apply catalog corrections in apps/web/src/localization.tsx and context-specific heading in packages/reality-core/src/reality/services/operational_previews.py; update matching browser fixture in apps/web/scripts/operational-previews-browser.mjs.

## US2: Preserve meaning
- [x] T004 [US2] [FR-003] Run existing preview/terminology/formatting checks, web-build, lint and spec policy; review unchanged keys/source boundaries; record results in specs/212-erp-language/verification.md and update docs/WEB_SPEC.md.

Dependencies: T001 → T002 → T003 → T004. No schema, API or business-rule work.
