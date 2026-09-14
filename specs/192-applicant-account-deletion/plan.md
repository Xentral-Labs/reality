# Implementation Plan: Applicant Account Deletion

**Language**: English

## Constitution Check

- No schema and no migration: the feature removes rows from tables that already exist and writes
  one audit event through the existing `security_audit_event` shape (rule 11). PASS
- Business rules stay server-side. The client mirrors only two things — whether a control is
  offered and whether the confirm button is enabled — and the server re-checks both before any
  write. PASS
- Authority is explicit. The routes sit on `admin_router` behind `PlatformAdmin`, the same guard the
  review and overview routes use; the service refuses the acting administrator and any
  `is_platform_admin` account before touching a row. PASS
- The tenant boundary is respected rather than widened. `require_business_operation` keeps refusing
  practice tenants for every business caller; the deletion reaches them through a private sweep that
  only platform administration can call, and the sweep is the one `permanently_delete_tenant`
  already performed — it is factored out, not weakened. PASS
- The isolation catalog is unaffected: discovery only classifies public functions that carry a
  `tenant_id` parameter, and neither `delete_account` nor `account_deletion_preview` does.
  `_purge_tenant_records` is private. No count changes. PASS
- No MCP tool, CLI command or API-token path is added; deletion stays an interactive,
  session-authenticated action. PASS

## Steps

1. Factor the tenant sweep out of `permanently_delete_tenant` into the private
   `_purge_tenant_records` in `reality.services.core`, with no behaviour change.
2. Service module `reality.services.account_deletion`: `account_deletion_preview` (reads only),
   `delete_account` (guards, sweep, reference cleanup, tombstone) and `application_account_id`.
   Derive both the sole-owner set and the reference cleanup from `Base.metadata`, never from a
   hand-written table list.
3. Service tests `packages/reality-core/tests/test_account_deletion.py` covering the purge, the
   surviving shared company, both guards, both confirmations and the tombstone, with a
   schema-driven assertion that no reference to the account remains.
4. Routes in `reality.web.auth`: `GET .../deletion-preview` and `POST .../delete` on the admin
   router, mapping `NotFound` to 404 and `InvalidOperation` to 400.
5. HTTP tests `packages/reality-core/tests/test_access_application_deletion_api.py` for both routes,
   the 403 for a non-administrator and the refusal that removes nothing.
6. Client rules module `apps/web/src/accessDeletion.ts` with `deletionConfirmationValid` and
   `deletionOffered`; contract test `apps/web/scripts/access-deletion.test.mjs` first. The module
   keeps its imports type-only so the test can load it directly.
7. `apps/web/src/Auth.tsx`: a Delete control on every row where it is offered, and a native
   `<dialog>` that loads the preview, names what is lost and gates its confirm button.
8. Styles in `apps/web/src/auth.css`; localization for de, nl and es with `DELETE` kept literal.
9. Gates: ruff, the two backend modules and the full backend suite, prettier, `npm run test:i18n`,
   `npm run i18n:audit`, `npm run build`, `make spec-check`.

## Rollback

Revert the commit. No migration and no data change of its own; a deletion already performed is not
reversible, which is what the two confirmations and the preview are for.
