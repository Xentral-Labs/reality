---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Read-and-Prepare Preset for Manual MCP Tokens

- [ ] T001 Owner approval of scope
- [X] T002 [US1] [FR-001] [FR-002] Extend `apps/web/scripts/unified-ai-access-browser.mjs` with
  the preset's selection and the absent approval warning
- [X] T003 Observe T002 failing against `origin/main`'s `MCPAccess.tsx` — the button is missing
- [X] T004 [FR-001] [FR-002] Add the preset in `apps/web/src/unified/MCPAccess.tsx`
- [X] T005 [FR-003] Add the label in `apps/web/src/localization.tsx` (de, nl, es)
- [X] T006 Run the browser proof, `npm run i18n:audit`, `npm run test:contracts`,
  `npm run build`, `make spec-check`

## Requirement Coverage

| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T002 | T004 |
| FR-002 | T002 | T004 |
| FR-003 | T006 (i18n audit) | T005 |
