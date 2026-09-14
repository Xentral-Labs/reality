# Quickstart: Validate Web UX Matrix Completion

## Prerequisites

- Local PostgreSQL test service and project dependencies are available.
- Spec 029 is merged into the validation base or recorded as a separate owner.

## Exhaustive UX coverage

From `apps/web`:

```bash
node --test scripts/ux-matrix-contract.test.mjs
npm run test:i18n
npm run i18n:audit
npm run build
```

Expected: every destination/matrix row has one owner and complete hierarchy, state,
explanation, responsive evidence, and deterministic drift diagnostics.

## Backend authority

From `packages/reality-core`:

```bash
pytest -q tests/test_ledger.py tests/test_master_data_api.py tests/test_http_boundary.py
```

Expected: UI-facing reads remain tenant-scoped, authoritative, bounded, and service-backed.

## Desktop/mobile review

1. Use deterministic empty and representative populated tenants.
2. Review every affected destination at desktop and representative mobile widths.
3. Verify job, first-viewport hierarchy, primary action, applicable states, and explanation.
4. Record results against the manifest; confirm zero browser errors and bounded tables.

## Complete gates

```bash
make lint
make test
make web-build
make spec-check
git diff --check
```

Only after executable evidence and owner final approval may `016/FR-006` become verified.
`016/FR-015` must remain documented.

## Implementation evidence — 2026-09-02

- Topology: `ux-matrix-v1` maps all 25 current routed/nested destinations;
  authentication/profile are explicit supporting scope and Spec 029 retains the
  global Activity drawer.
- Operational/configuration/support: the dedicated Node contract families pass
  against the existing business-first hierarchy, shared states, confirmation
  boundary, and shortest-link Inspector behavior.
- Finance/Evidence: Journal is now a canonical Finance destination backed by a
  tenant-scoped SQL read. It exposes full-filter debit/credit/balance totals,
  account/date/query controls, a 50-row default and 100-row maximum, and working
  ledger-entry/document Inspect entrypoints.
- Responsive/state structure: shared `br-*` page, control, table, dialog, drawer,
  and empty-state primitives are enforced. Tables retain bounded horizontal
  scrolling and the mobile navigation contract remains explicit.
- Localization: `en`, `de`, `nl`, and `es` each pass at 708/708 strings with zero
  missing or invalid entries.
- Schema inventory: 50 SQLAlchemy business tables and 29 migration versions before
  and after; the diff contains no model, catalog, or migration change.

Exact automated results:

```text
Ruff: PASS
Focused backend/API/policy: 46 passed
Complete PostgreSQL suite: 245 passed, 7 skipped
Product Web contracts: 33 passed
Localization audit: 708/708 PASS for en/de/nl/es
Production Web build: PASS (non-blocking existing chunk-size advisory)
Prettier check: PASS
git diff --check: PASS
```

The compatible automated browser runtime was unavailable, so the owner reviewed
the isolated Product Web environment directly. After a clean review-server restart,
the owner accepted the visual result as “looks good” on 2026-09-02. The completed
desktop/mobile record is in `checklists/visual-review.md`.

The product owner approved final review on 2026-09-02. Baseline `016/FR-006` is
therefore `Verified as-is`, its coverage-gap row is removed, and the dedicated
policy regression protects that result. `016/FR-015` remains unchanged as the
single accepted Documented gap.

Final closure rerun:

```text
Ruff: PASS
Complete PostgreSQL suite: 246 passed, 7 skipped
Spec policy: PASS
Product Web contracts: 33 passed
Localization audit: 708/708 PASS for en/de/nl/es
Prettier and production build: PASS
git diff --check: PASS
```

Post-Spec-029 rebase verification:

```text
Rebased onto main at fc8a195 (global Activity drawer)
Ruff: PASS
Complete PostgreSQL suite: 251 passed, 7 skipped
Spec policy: PASS
Product Web contracts, including Activity integration: 35 passed
Localization audit: 717/717 PASS for en/de/nl/es
Prettier and production build: PASS
git diff --check: PASS
```
