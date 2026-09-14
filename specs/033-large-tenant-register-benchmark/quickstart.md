# Quickstart: Large-Tenant Register Benchmark

This is the planned acceptance workflow. The full run requires a disposable PostgreSQL
database; never point it at production or a shared development database.

## Prerequisites

- Python 3.12+ and `packages/reality-core` development dependencies.
- Repository-supported PostgreSQL with current migrations.
- A dedicated empty database whose name begins with `reality_benchmark_` and that may
  receive deterministic benchmark data.

## Fast contract gate

From `packages/reality-core`:

```bash
PYTHONPATH=src:. python -m pytest -q tests/test_large_tenant_register_contract.py
```

Expected: the reduced profile exercises the same nine-family catalog, query/result
contracts, tenant sentinel and report validation as the full profile.

## Full dataset and two-run proof

Set `REALITY_DATABASE_URL` to the dedicated database, then run:

```bash
PYTHONPATH=src:. python -m benchmarks.large_tenant_registers.runner \
  --profile full \
  --seed 32010 \
  --business-date 2026-09-01 \
  --repeat 2 \
  --confirm-disposable \
  --output ../../specs/033-large-tenant-register-benchmark/evidence/benchmark-result.json
```

Expected:

- at least 10,000 distinct same-day orders and all related cardinalities validate;
- both runs execute identical required cases;
- rows/samples remain bounded and tenant-isolated;
- expected totals, aggregates and adjacent-page identities match;
- applicable query-boundary evidence passes;
- Pydantic-validated JSON and Markdown evidence appear only after validation and retain
  neutral names until the product-owner final review accepts the complete diff.

## Evidence and final gates

Review the JSON against `contracts/benchmark-result.schema.json`, the derived Markdown,
sample traceability and any benchmark-proven read remediation. Durations are observations,
not universal latency guarantees.

```bash
ruff check .
pytest -q
cd ../..
python3 scripts/check_spec_policy.py
```

Only after these gates and final owner review may Spec 016 close FR-015/SC-007 and the
capacity idea record this feature as established groundwork.
