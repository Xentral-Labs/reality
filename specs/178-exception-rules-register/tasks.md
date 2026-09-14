# Tasks: Exception Rules Register

**Language**: English

- [x] T001 Add `class_id` filter and `attention_summary` to `reality.services.attention_reads`.
- [x] T002 Expose the filter and `GET …/attention/summary` in `reality.web.api`.
- [x] T003 Service tests for filter, refusal and summary; HTTP boundary assertions.
- [x] T004 Build `ExceptionRulesRegister` (table, open count, inline preview with open findings).
- [x] T005 Wire the Inspector exceptions tab; reduce `ExceptionCatalog` to the dialog.
- [x] T006 Localize new strings (de, nl, es); run the i18n audit.
- [x] T007 Update `unified-inspector-browser.mjs`; run a focused browser check (en, de, 390px).
- [x] T008 Run ruff, the attention and operations test modules, tsc, prettier and contract tests.
- [x] T009 Expose the resource catalog's translated class labels through the exception catalog read and show them in the register and the dialog.

## FR-007 regression correction (2026-09-12)

- [x] T010 Restore the German dictionary assignment for the four exception-register strings. They had been appended to the preceding Spanish dictionary block during integration. The existing i18n audit reproduced all four missing German entries before the fix and passes for en/de/nl/es after it.
- [x] T011 Run `make web-build`: formatting, 125 frontend contract tests, all-language audit and TypeScript/Vite production build passed. No business behavior or schema changes are introduced.
