# Tasks: Company Danger Zone

**Language**: English

- [x] T001 Contract test `apps/web/scripts/company-lifecycle.test.mjs` for the archive guard, the archived filter, the delete confirmation and the loss summary (FR-001, FR-002, FR-005).
- [x] T002 Rules module `apps/web/src/unified/companyLifecycle.ts` (FR-001, FR-002, FR-005).
- [x] T003 Component `apps/web/src/unified/CompanyDangerZone.tsx`: archive row, archived list, archive and delete dialogs, bootstrap reload (FR-003, FR-004, FR-006, FR-007).
- [x] T004 Mount in `CompanySettings.tsx`; add `.br-btn-critical` to `tailwind.css`.
- [x] T005 Localize new strings (de, nl, es); keep `DELETE` literal (FR-008).
- [x] T006 API test: member receives 403 on archive, restore and delete (FR-009).
- [x] T007 Browser script `apps/web/scripts/company-danger-zone-browser.mjs`; run at 1440px and 390px, English and German (SC-001, SC-002, SC-003).
- [x] T008 `docs/WEB_SPEC.md` paragraph on the Danger zone.
- [x] T009 Gates: prettier, `test:i18n`, `i18n:audit`, `build`, ruff, backend modules, `make spec-check`.
- [x] T010 `archive_run` / `restore_run` in `reality.services.playground` with service test (FR-010).
- [x] T011 `POST /api/playground/runs/{id}/archive|restore` with HTTP test (FR-011).
- [x] T012 Sandbox row, archived sandboxes list, client helpers, translations, browser flow (FR-012).
