# Quickstart: Workspace Views and Actions

## Focused automated proof

```bash
make spec-check
cd packages/reality-core
../../.venv/bin/pytest -q tests/test_application_catalog.py tests/test_http_boundary.py tests/test_inventory_tracking_reservations.py tests/test_inventory_and_fulfillment.py tests/test_commitment_holds.py tests/test_handling_units.py tests/test_movement_corrections.py
cd ../../apps/web
npm run test:contracts
npm run i18n:audit
npm run build
```

Expected: catalog drift is rejected; Warehouse commands remain tenant scoped; Views and Actions render with confirmation and translated states; the production bundle succeeds.

## Manual acceptance story

1. Select Warehouse Operations in an empty company and verify stable `Views` and `Actions` plus prerequisite guidance.
2. In a seeded company, start `Record movement`, enter valid business inputs, and verify no write occurs before confirmation.
3. Confirm and verify Movements refreshes and the result is inspectable.
4. Verify a stale movement-correction preview is refused.
5. Repeat representative reserve, hold/release, handling-unit, lot, and serial actions.
6. Switch workspaces and verify company, records, calculations, and permissions remain unchanged.
7. Repeat desktop/mobile navigation and dialogs in all supported languages.

## Full gates

```bash
make lint
make test
make web-build
```

Do not mark tasks complete while a required check is red.

## Verification evidence (2026-09-03)

- Initial frontend proof: 3 expected failures for missing catalog navigation, confirmation, and explicit clients.
- Catalog and Warehouse PostgreSQL proof: 52 passed.
- Complete backend suite: 366 passed, 7 skipped.
- Frontend contracts: 51 passed.
- Localization audit: 803/803 covered for each of English, German, Dutch, and Spanish.
- Production frontend build: passed; the existing bundle-size advisory remains non-blocking.
- Specification policy, Ruff, and diff whitespace checks: passed.
- Desktop/mobile browser verification: attempted, but no browser backend was connected to this session; manual visual acceptance remains open.
- Company Activity amendment: Activity appears once under Company Overview Views, opens the full Activity page, and has no competing desktop/mobile header control or global drawer. Verification passed with 23 catalog tests, 52 frontend contracts, the strict 793/793-per-language i18n audit, production build, lint, and spec policy.
- Empty-company regression: Company Overview Views now remain visible while `Get started` is rendered as an additional group. The 4 focused workspace contracts, strict 795/795-per-language i18n audit, production build, lint, spec policy, and diff check passed. The complete frontend contract run currently has one unrelated Ask Reality assertion mismatch because `isEmpty` now also checks archive state; T047 remains open until that concurrent contract change is reconciled.
- Order action launcher amendment: Order Operations promotes reservation and commitment hold/release, while `More actions` searches all four validated Web-eligible Order action families and starts their existing explicit confirmation flows. Verification passed with 24 catalog tests, 53 frontend contracts, strict 800/800-per-language i18n coverage, production build, lint, spec policy, and diff check. The prior concurrent Ask Reality contract mismatch is resolved and T047 is closed.
- Generic workspace disclosure amendment: every actionable workspace now shows at most its first two canonically ordered actions directly and always exposes the complete set through the same searchable launcher. Workspace-specific promotion metadata was removed. Verification passed with 23 catalog tests, 53 frontend contracts, strict 799/799-per-language i18n coverage, production build, lint, spec policy, and diff check.
- Complete Web adapter amendment: manual order, source-supported Fact observation, customer payment, and supplier payment now have explicit tenant-scoped endpoints, typed clients, confirmed forms, localized labels, and workspace classifications. The manual-order route delegates to the canonical atomic Source → Evidence → Reality service. Verification passed with 28 focused catalog/HTTP tests, 54 frontend contracts, strict 799/799-per-language i18n coverage, the complete backend suite (367 passed, 7 skipped), production build, lint, spec policy, and diff check.
