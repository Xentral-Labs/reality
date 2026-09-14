# Validation

Run apps/web npm run test:contracts, npm run i18n:audit, npm run format:check and npm run build. Run scripts/retirement-browser.mjs against a local Vite build for fixture-based entry/navigation coverage. Verify /app without VITE_UNIFIED_APP, old tenant-qualified warehouse/finance bookmarks, /playground/runs/saved, unknown app paths, signed-out login and pending approval. No compatibility navigation may issue a business mutation.

Run the full PostgreSQL backend suite, docs/site quality gates, make spec-check and git diff --check. Preserve the previous deployment artifact for rollback; this PR does not deploy.

## Verification evidence — 2026-09-08

- Failing-first route test: missing entryRouting module before implementation.
- Frontend: 39 retained/retirement tests passed; formatting, build and four-language audit passed (1045 keys). Legacy-only presentation tests were retired with the removed screens; current unified contracts and proxy/theme/localization checks remain.
- Retirement browser: sole app without a flag, old register/tenant links, shared exception catalog, unknown routes, retired entry/run paths, pending approval, signed-out account returns and mobile overflow passed. Zero navigation writes and zero runtime errors. Desktop/mobile screenshots were inspected.
- Existing Inspector browser: graph, catalogs, forms, projection data, reload, rule simulation/review/create/draft and tenant/member boundaries passed.
- Backend: 1796 passed, 7 existing skips, using four workers and isolated PostgreSQL databases. The first run identified missing spec metadata; after correction the complete suite passed. No runtime backend or migration files changed.
- Docs: 45 tests plus formatting/build passed. Site: 55 tests plus formatting/localization/build passed. Ruff, spec policy and diff whitespace checks passed.
- Final review: no records, migrations, backend authorization or business-service implementations removed. Shared catalog styles live in retained tailwind.css. Current main is the branch base.

This verification covers the requested source retirement, not a live deployment or deletion of retained sandbox APIs.

## Profile menu and personal-settings separation

FR-007/008 verification: 39 frontend contracts, formatting, four-language audit
(1050 keys) and production build pass. The extended retirement browser passes
profile identity/resources, Escape, separate personal/company settings navigation,
failed logout followed by explicit successful retry, mobile menu bounds and all
previous retirement scenarios. Only the two explicit fixture logout requests write.
Desktop/mobile menu screenshots were inspected. The first browser run proved the
missing Profile trigger; the settings routing test failed before changing the default
from personal to company. The local Docker web image was rebuilt on port 8080;
backend services and stored data are unchanged.

## Company management follow-up
FR-009/010: browser scenario first failed waiting for the missing Companies region. Added all authorized companies, current selection, owner/member guidance, company-scoped user/token shortcuts and separate creation. Manage companies replaces the generic sidebar label; agent tokens have their own tab. Frontend contracts: 39 passed. Locale audit: 1,053 keys in all four languages passed. Production TypeScript/Vite build and formatting passed. No backend/schema/service changes; prior complete backend evidence remains applicable.

Final browser acceptance passed on the refreshed Docker app at localhost:8080: all companies, owner/member guidance, current marker after reload, cross-company user management, dedicated tokens versus provider settings, member direct-link denial, separated creation, profile/logout/mobile and retained routing/auth boundaries. Only the two explicitly simulated logout requests wrote; company browsing and management navigation performed no writes. Screenshot reviewed at /private/tmp/company-settings.png. Diff and spec-policy review passed.

## Final focused-dialog UX (FR-009 clarification, FR-011)
Replaced the intermediate management tabs with focused native dialogs. Companies always opens the list; management targets remain independent of the working company. New company is a top-right modal action. Final checks: 39 frontend contracts; all 1,050 extracted keys in four languages; TypeScript/Vite production build; formatting and spec policy passed. Browser acceptance on refreshed Docker localhost:8080 passed: owned-company user/token management while a member company remains active, unchanged URL, correct t1 API reads, no t2 privileged reads, member direct-link denial, task separation, explicit switch/reload, creation dialog, Escape/focus restoration and retained profile/auth coverage. User and token modal screenshots reviewed. Only explicit fixture logout requests wrote. Existing backend/service confirmation behavior is unchanged.

Home CTA terminology correction: “Review commitments” and its German/Dutch/Spanish translations replace “Review deliveries”. Destination unchanged. All 1,050 locale keys, TypeScript/Vite build, formatting and diff review pass. Local Docker web refreshed on port 8080. No new test for this label-only change.

Commitment label alignment: Home/Your work titles, search/empty/prompt, order links and case back navigation aligned; Your work explicitly identifies open customer delivery commitments. 39 frontend contracts, 1,052 localized keys in four languages, production build, formatting and spec policy passed. Existing unified-orders-browser passed order drilldown, customer case, incoming Inspector, keyboard/reload, filters/paging, error/company boundaries, no writes and 48 localized screenshots. An earlier browser run overlapped the Docker restart; the final run completed after refresh. Local app remains on port 8080.

FR-012 verification: 39 frontend contracts, localization (1,052 keys/four languages), production build, formatting, diff and spec-policy checks passed. Existing order browser suite now verifies automatic first commitment/detail selection, one history step from Home, mobile back without reselection, explicit unavailable ID preservation, and empty lists. Full browser run passed alongside existing order/tenant/no-write checks and 48 localized screenshots. Test setup closes the mobile chat overlay before list interaction. Corrected the receipt-modal browser selector to retain its unchanged delivery-specific label. Local Docker web refreshed at port 8080.

FR-013 final verification: 39 frontend contracts, 1,049 locale keys/four languages, production build, formatting and spec policy passed. Browser register/detail coverage passed row click/Enter, customer actions, supplier receipt availability, filter/page preservation on explicit return and browser Back, unavailable legacy links, empty legacy list, prior order/evidence/tenant checks and 48 localized screenshots without writes. Account/navigation suite passed Home-to-register, absent Your work link, profile/company/auth/mobile checks. Existing delivery/shell tests were aligned with new navigation and the delivery fixture now includes the canonical type. Local Docker web refreshed on port 8080. Register stays mounted; scroll capture/restore and table identity reviewed. No backend changes.
