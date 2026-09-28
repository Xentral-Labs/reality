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
