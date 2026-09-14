# Validation

## Commands and evidence

- Backend targeted: `PYTHONPATH=src ../../.venv/bin/pytest tests/test_unified_delivery_holds.py -q` from packages/reality-core: **8 passed**. Covers own/customer scope, unchanged goods/reservations, exact plural release, stale replacement, confirmation/replay, unknown outcome recovery, malformed inputs, actor checks, practice boundary and HTTP/tool parity.
- Catalog and tenant boundary regression suite: **49 passed** after keeping shared hold validation internal. The first full run found only nine instances of that catalog drift; no new public service is declared.
- Full PostgreSQL suite: **1530 passed, 7 existing skips** in 270.66 seconds (`/private/tmp/reality-117-backend-verified.log`).
- Frontend `npm run test:contracts`: **131 passed**. `npm run build`, `npm run format:check`, `npm run i18n:audit`: passed, **1553/1553** entries covered in each of English, German, Dutch and Spanish. Existing build chunk advisory remains.
- `scripts/unified-holds-browser.mjs`: case hold/release, canonical reason and original note, no preparation effects, exact review, edit/reload/confirmation, retained customer hold, shared catalog/launcher and Chat/Decisions entry. Sixteen localized desktop/mobile screenshots using the actual `data-theme` selector; German light desktop and dark mobile renders visually inspected. Screenshots in `/private/tmp/reality-117-browser`.
- Existing `scripts/unified-delivery-browser.mjs` and `scripts/unified-receipt-release-browser.mjs`: passed. The receipt/release screenshot harness now sets the actual `data-theme` selector; this corrects validation, with no application behavior change.
- Authenticated isolated preview: real catalog discovery and service-backed hold proposal, URL reload and rejection passed (`/private/tmp/reality-117-live.log`). No hold was applied in the preview company.
- Spec policy, Ruff and diff checks passed. Final review found no remaining implementation gap in this bounded increment.

## Review

No schema or migration. Shared core validation and existing tenant lock remain the authority. Hold events carry the confirmed action identity; receipt verification matches exact own holds and preserves creation proof after later release. Customer-wide holds remain separate. The launcher resolves related services from the existing combined hold/release declaration rather than inventing an extra capability. Original notes render as escaped text. Quantity/tracking controls do not appear for holds; counts use no stock unit.

Preview: `http://127.0.0.1:5177/app/work?tenant=ten_7bcf46fd38`, API port 8007, isolated local sample company. No production deployment, party/document hold editor or legacy retirement is included.

## Current local connection (2026-09-08)

At the owner's request the active review URL is now `http://localhost:5177/app/home`.
API 8007 uses the same `reality_test` database and users/tenants as port 8080; the
existing owner login and shared session were verified, with five identical company
identities. The isolated sample-based evidence above remains historical validation;
no hold mutation was performed when checking the shared connection. See the local
runtime instructions in `../139-unified-app-foundation/quickstart.md`.
Spec impact: none — local configuration only; existing authentication and tenant
contracts are unchanged.
