# Tasks: Applicant Account Deletion

**Language**: English

- [x] T001 Factor `_purge_tenant_records` out of `permanently_delete_tenant` in `reality.services.core` without changing its behaviour.
- [x] T002 Service module `reality.services.account_deletion` with `account_deletion_preview`, `delete_account` and `application_account_id` (FR-002, FR-004 – FR-010).
- [x] T003 Service tests `tests/test_account_deletion.py`, including the schema-driven proof that no reference to the account remains (SC-003).
- [x] T004 Routes `GET .../deletion-preview` and `POST .../delete` on the platform-admin router (FR-011).
- [x] T005 HTTP tests `tests/test_access_application_deletion_api.py` for both routes, the 403 and the refusal that removes nothing (FR-011).
- [x] T006 Contract test `apps/web/scripts/access-deletion.test.mjs` for the confirmation and the offered control (FR-001, FR-003).
- [x] T007 Client rules module `apps/web/src/accessDeletion.ts` (FR-001, FR-003).
- [x] T008 Delete control and confirmation dialog in `apps/web/src/Auth.tsx` with the preview (FR-001, FR-002).
- [x] T009 Styles in `apps/web/src/auth.css`.
- [x] T010 Localize the new strings (de, nl, es); keep `DELETE` literal (FR-012).
- [x] T011 Wrap `/admin` and `/admin/access` in `LocalizationProvider` so their dictionaries reach the DOM (FR-013).
- [x] T012 Browser proof `apps/web/scripts/access-deletion-browser.mjs`: offered and withheld controls, the preview, the gated confirm, a server refusal, the confirmed payload and German at 390px (SC-001, SC-004, SC-006).
- [x] T013 Gates: ruff, backend suite, prettier, `test:i18n`, `i18n:audit`, `build`, `make spec-check`.
