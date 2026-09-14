# Implementation Plan: Company Danger Zone

**Language**: English

## Constitution Check

- No schema, no new authority: the zone renders the existing lifecycle endpoints and the usage
  counts the companies endpoint already derives (rule 11). PASS
- Business rules stay server-side. The client repeats the guards (owner, practice company, last
  active company, exact confirmations) only to explain a disabled control; every action still
  goes to `archive_tenant`, `restore_tenant`, `permanently_delete_tenant` through the API. PASS
- Tenant boundary unchanged: `require_company_owner` on every endpoint, playground tenants
  refused by `require_core_operation`; a new API test proves the 403 for members. PASS
- No MCP, CLI or token surface is added; the actions remain interactive. PASS
- Sandboxes: `archive_run` / `restore_run` reuse the run status vocabulary that restart and
  storyline restart already write; owner-only through `require_playground_run`, confirmed
  explicitly; no tenant row changes. Neither function carries `tenant_id`, so the isolation
  catalog discovery is unaffected. PASS

## Steps

1. Client rules module `apps/web/src/unified/companyLifecycle.ts`: `archiveGuard`,
   `archivedCompanies`, `deleteConfirmationValid`, `lossSummary`, the literal confirmation word.
   Contract test `apps/web/scripts/company-lifecycle.test.mjs` first.
2. Component `apps/web/src/unified/CompanyDangerZone.tsx`: section with the archive row for the
   selected company, the archived list read from `api.companies()`, native `<dialog>`
   confirmations (same shape as `CompanyManagementDialog`), busy and alert states. After archive
   or restore: `api.bootstrap()` then `openCompany`.
3. Mount the zone at the end of `CompanySettings`; add the `.br-btn-critical` control variant to
   `tailwind.css` next to `.br-btn-primary`.
4. Localization for de, nl, es; `DELETE` displayed as original text.
5. Backend test in `test_master_data_api.py`: a logged-in member receives 403 on archive, restore
   and delete while the owner path stays green; the lifecycle tests in `test_tenant_lifecycle.py`
   remain the service proof.
6. Browser proof `apps/web/scripts/company-danger-zone-browser.mjs` with HTTP fixtures: archive
   flow with bootstrap reload, disabled reasons (last active, member, practice), delete dialog
   gating and payload, restore, server refusal, German at 390px.
7. Docs: one paragraph in `docs/WEB_SPEC.md` under the Companies settings description.
8. Sandboxes: service functions in `reality.services.playground`, routes in `reality.web.playground`,
   service and HTTP tests, client helpers `sandboxRuns` / `archiveSandbox` / `restoreSandbox`, the
   sandbox row and the archived sandboxes list in the zone.
9. Gates: prettier, `npm run test:i18n`, `npm run i18n:audit`, `npm run build`, ruff, the two
   backend test modules, `make spec-check` after the commit.

## Rollback

Revert the commit. No migration, no data change; the endpoints existed before.
