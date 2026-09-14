# Quickstart: Business-readable Inspectors

1. Open a source-backed Boolean Fact for an order Commitment.
2. Confirm the first viewport explains the observation and false/true value, names the
   source order reference, identifies the affected subject in business language, and
   offers no invented action.
3. Expand Technical details and confirm Fact ID, subject ID, exact predicate, source ID,
   events, and original source payload remain available.
4. Open two same-titled Commitment Exceptions from different orders and confirm their
   first view names different business references, cause, impact, and review guidance.
5. Follow a linked record and confirm the drawer retains the same hierarchy and tenant.
6. Repeat for Document, Reservation, Movement, Payment, Party, Item, and Location.
7. Repeat at 390 px width and verify business content has no horizontal scroll.

Required gates:

```bash
make spec-check
make lint
cd packages/reality-core && ../../.venv/bin/pytest -q tests/test_master_data_api.py
cd apps/web && npm run test:contracts
cd apps/web && npm run i18n:audit
make web-build
```

Expected: an ERP consultant can understand the business record first and can still
reconstruct every exact technical link on demand.

## Verification evidence

- Complete master-data API and Inspector stories: 35 passed.
- Complete frontend contract suite and localization audit: 80 passed; all 4 languages
  complete.
- TypeScript production build: passed (Vite reports only the existing bundle-size
  advisory).
- Browser visual review: pending because no controllable local browser was available in
  the implementation environment. Desktop and 390 px checks remain required before the
  feature is marked fully reviewed.
