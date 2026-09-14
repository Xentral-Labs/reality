# Quickstart: Validate Master Data Adapter Parity

## Matrix and canonical-state proof

```bash
cd packages/reality-core
pytest -q tests/test_master_data_parity.py
```

Expected: 36 cells declared; real CLI/API operations produce equivalent canonical
state; failures are atomic/non-disclosing; lifecycle preserves source/history links.

## Product Web action proof

```bash
cd apps/web
node --test scripts/master-data-parity.test.mjs
npm run build
```

Expected: actual create/edit/toggle actions map to correct API methods and tenant routes,
with no browser-owned persistence or business rules.

## Complete gates

```bash
make lint
make test
make spec-check
make web-build
git diff --check
```

Expected: all gates pass and no model or migration changes exist.

## Manual review

1. Create, update, deactivate, and reactivate equivalent Party, Item, and Location
   records through CLI and Product Web.
2. Inspect authoritative records and confirm business values match.
3. Confirm IDs and source/history links remain stable.
4. Confirm browser actions use normal JSON API requests.
5. Confirm formatting differences are ignored but business differences fail.

Only after executable evidence and final owner approval may `004/FR-016` be marked
verified and its coverage row removed.

## Implementation evidence (2026-09-02)

- Focused Core adapter/API/CLI proof: 38 passed, including real paired CLI/API
  create, update, deactivate, and reactivate sequences for all three families.
- Product Web contract: 14 passed; production build passed.
- Full PostgreSQL run from `packages/reality-core`: 237 passed, 7 skipped.
- Spec policy, Ruff, and `git diff --check`: passed.
- One real drift was found and corrected: Location update now forwards optional source
  system, external ID, and complete payload from JSON API/Web to the existing shared
  source-versioning service.
- No model or migration change was introduced.
- Product-owner final review was approved; `004/FR-016` is now `Verified as-is`, its
  accepted-gap row is removed, and the three unrelated accepted gaps remain open.
