# Validation Quickstart: Complete Tenant Isolation Coverage

## Prerequisites

- Python 3.12+
- Repository development environment installed
- Local PostgreSQL test service available
- Spec 019 catalog and isolation tests present

## 1. Validate Catalog Discovery

Run the focused catalog/inventory tests from `backend/`. Every discovered operation,
projection, tool, and canonical catalog service must map to one family or exemption.
Add a temporary uncovered fixture operation: the test must fail and name it. Restore the
fixture before continuing.

## 2. Run Read and Collection Evidence

Use the populated two-tenant graph. Foreign IDs must behave like unknown IDs, and no
foreign sentinel may appear in local lists, searches, details, registers, timelines, or
projections. An empty foreign tenant is not sufficient proof.

## 3. Run Aggregate Evidence

Use asymmetric quantities, money, event counts, and projection rows. Local counts,
stock, balances, open amounts, and summaries must equal local-only expectations.

## 4. Run Mutation and Relationship Evidence

Execute Tenant A actions with Tenant B IDs. Compare row counts, events, quantities,
balances, and record state before/after. Expect non-disclosing failure and zero side
effects in both tenants.

## 5. Run Tool and Adapter Evidence

Run application-tool and representative Web/API tenant-context checks. These prove
propagation into shared services and do not replace service-family evidence.

## 6. Run Repository Gates

```bash
python3 scripts/check_spec_policy.py
cd backend
../.venv/bin/ruff check <changed-python-files>
TEST_POSTGRES_DATABASE_URL=postgresql+psycopg://reality:local-only@localhost:54329/reality_test ../.venv/bin/pytest -q
```

Expect focused and full PostgreSQL suites to pass. No frontend change is planned.

## 7. Close the Baseline Gap Last

After all evidence and owner review pass, change only `003/FR-012` to `Verified as-is`,
remove only that gap from `docs/SPEC_COVERAGE_MATRIX.md`, and preserve all unrelated
gaps. Record initial uncovered counts, defects, final family/operation counts, commands,
and owner acceptance here during implementation.

## Implementation Evidence

- Initial and final discovered surface: 166 operations in six isolation families.
- Registry surface: 13 operational projections and 13 application tools.
- Catalog failures covered: missing, stale, duplicate, invalid classification,
  overbroad exemption, empty evidence, unproven operation, and registry drift.
- Read/collection/aggregate outcome: no defect found in shared production services.
- Mutation/relationship outcome: no defect found; the controlled foreign relationship
  failed before persistence and both tenant row/event snapshots remained unchanged.
- Adapter outcome: application-tool and representative HTTP/API tests preserved tenant
  context; no adapter-specific business rule was introduced.
- Final focused command covering the catalog, family evidence, tools, representative
  API, and spec policy → 53 passed.
- Full backend PostgreSQL command: `pytest -q` → 158 passed, 7 skipped.
- Schema/migration changes: none.
- Baseline change: only `003/FR-012`; accepted gap count changed from 10 to 9.
- Owner acceptance: final review approved on 2026-08-31.
