# Quickstart: Journey Proof Stories

Run from the repository root with the shared virtual environment.

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q \
  tests/scenarios/test_catalog_orders_and_shipments.py \
  tests/scenarios/test_catalog_stock_and_returns.py \
  tests/scenarios/test_catalog_finance.py \
  tests/test_business_journey_catalog.py \
  tests/test_business_journey_questions.py
cd ../..
make docs-generate
make docs-catalog-check   # after staging the regenerated payload
make spec-check
```

Expected: every story passes; each promoted journey shows `supported` in
`apps/docs/public/generated/business-journeys.json`; A19 and F07 (if they stay partial)
carry their finding as the public limitation.

Check the Guide answer for one promoted journey (SC-004):

```bash
PYTHONPATH=packages/reality-core/src .venv/bin/python -c "
from reality.services.business_journeys import answer_public_question, journey_catalog
answer = answer_public_question(journey_catalog(), 'Customer withdraws within 14 days and gets a full refund', locale='en')
print(answer.status, [match.id for match in answer.matches])"
```

Expected: `supported` with `F01` among the matches, once F01 is promoted.

## Evidence (2026-09-28)

After rebasing onto `d22f1953` (PR #243 merged):

- The three catalog modules pass (31 tests with `test_catalog_purchasing.py`); `tests/scenarios` passes in full (66).
- Catalog, question and API tests: 42 passed.
- The published Guide shows 81 supported, 70 partial, 74 missing and 3 out of scope (before: 70 and 81).
- Asking the Guide by each journey's title returns `supported` with the journey cited first for
  A04, A06, A07, A19, C04, F01, F05, M08, N01, N02 and N06, and `partial` for F07.
  The script needs `REALITY_DATABASE_URL` set to any PostgreSQL URL; it does not connect.
