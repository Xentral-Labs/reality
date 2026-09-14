# Validation

Use the isolated local PostgreSQL test database and unified frontend preview.

1. Run `PYTHONPATH=src ../../.venv/bin/pytest tests/test_unified_receipt_release.py` from packages/reality-core; then the full pytest suite.
2. In apps/web run `npm run test:contracts`, `npm run i18n:audit`, format check and build.
3. Run the receipt/release browser journey: incoming delivery → review partial receipt → confirm → inspect; active reservation → review full release → confirm → inspect. Repeat via launcher, reload the proposal and check Decisions/Chat entries. Cover no records, failures, keyboard and light/dark desktop/mobile.
4. Run existing delivery, orders and warehouse browser regressions and spec policy/Ruff/diff checks.

## Verified results — 2026-09-07

- Full backend: **1522 passed, 7 existing skips**, 278.70 seconds; `/private/tmp/reality-116-backend-verified.log`.
- Targeted new and existing delivery action suite: **23 passed**; `/private/tmp/reality-116-pool-final.log`. The initial six missing-feature tests and alternate-destination pool test were observed failing before implementation.
- Frontend: **131 contracts passed**, **1541/1541 translation coverage** in all four languages; build, format check, Ruff, spec policy and diff checks pass.
- New browser journey passes contextual receipt/release, launcher discovery from actual command metadata, exact intent, edit after reload, fresh review, confirmation, empty selection and 16 localized release-review layouts plus mobile/desktop empty states. `/private/tmp/reality-116-browser-final.log`; screenshots in `/private/tmp/reality-116-browser/`.
- Existing delivery, Orders and Warehouse/Attention browser journeys pass; their logs are `/private/tmp/reality-116-delivery-browser.log`, `/private/tmp/reality-116-orders-browser.log`, `/private/tmp/reality-116-operations-browser.log`.
- Authenticated isolated sample preview discovers both actions and prepares real API receipt/release reviews. Reviews were rejected without stock effects. `/private/tmp/reality-116-live.log`; live review screenshots were visually inspected.

Final review: no schema, source authority or new tool schema. Release remains whole-reservation only. Canonical action execution checks both commitment and actual destination stock pools. Receipt/release proof uses action events and exact records; recovery never repeats execution. Existing company/practice separation and legacy compatibility remain.

No rollout or retirement is authorized by technical checks alone.


## Action form layout correction — 2026-09-08

FR-006 now explicitly defines 16px field-group gaps and pagination only for multiple
record pages. The shared form uses a column layout so label groups participate in
spacing. Multi-page controls and the page indicator align in a separate row. No
service, proposal or execution behavior changes.

Regression: `ACTION_LAYOUT_ONLY=1` with `unified-receipt-release-browser.mjs` first
failed on the visible one-page pager, then passed hidden single-page navigation,
working previous/next navigation, aligned controls and measured gaps at 390/1440px.
Build, 131 frontend contracts, spec policy and diff checks pass. Screenshots were
visually reviewed. No backend rerun is needed for this presentation-only correction.
