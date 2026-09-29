# Quickstart: Journey Proof Stories, Round Two

```bash
cd packages/reality-core
PYTHONPATH=src ../../.venv/bin/python -m pytest -q \
  tests/scenarios/test_catalog_purchasing.py \
  tests/scenarios/test_catalog_orders_and_shipments.py \
  tests/scenarios/test_catalog_sources.py \
  tests/scenarios/test_catalog_finance.py \
  tests/test_movement_create_readiness.py \
  tests/test_business_journey_catalog.py tests/test_business_journey_questions.py
cd ../..
make docs-generate && make docs-catalog-check   # after staging
make spec-check
```

Guide check for each promoted journey (SC-004), English and German:

```bash
REALITY_DATABASE_URL=postgresql+psycopg://x@localhost/x PYTHONPATH=packages/reality-core/src \
.venv/bin/python -c "
from reality.services.business_journeys import answer_public_question, journey_catalog
a = answer_public_question(journey_catalog(), 'Supplier delivers less and the rest never comes', locale='en')
print(a.status, [m.id for m in a.matches][:3])"
```
