# Quickstart: Verify the Demo Contribution Portfolio

## Prerequisites

- PostgreSQL test service available at the repository test URL.
- Python environment installed according to the repository setup.

## Focused business-story proof

Run:

```bash
.venv/bin/pytest -q packages/reality-core/tests/test_demo_costing_profile.py
```

Expected:

- The profile reports version 3.
- `costing_cases` contains the three retained cases and five new complete portfolio cases.
- Six complete outcomes include healthy positive, lower positive, and negative DB2.
- Selling-cost compositions reconcile exactly and remain source-backed.
- Missing-cost and late-cost/return cases remain truthful.
- Replaying setup does not increase source, review, match, or assignment counts.

## Documentation proof

Run:

```bash
cd apps/docs
npm test
npm run build
```

Expected: the profile contract and business handbook describe the expanded portfolio, its arithmetic, intentional gaps, and boundary from continuous Demo Data.

## Repository gates

Run:

```bash
make spec-check
make lint
make test
make web-build
cd apps/web && npm run i18n:audit
```

Expected: all commands pass. This feature requires no migration.

## Manual business review

1. Create a new company with Demo Data after the profile initialization worker is running.
2. Open Finance and locate the stable `COST-PORTFOLIO-*` invoices.
3. Expand each invoice and open its contribution explanation.
4. Confirm that the complete examples expose exact revenue, acquisition cost, selling costs, DB1, DB2, rate, and trace.
5. Compare the negative outcome with the deliberate missing-cost case: negative is a calculated result; missing remains unknown.

## Recorded verification (2026-09-20)

- Focused profile and security proof: 6 passed.
- Complete international-demo acceptance story: 25 passed in 196.12 seconds.
- Adjacent company-setup and Demo Data lifecycle regression set: 10 passed.
- Documentation: formatting passed, 76 contract tests passed, production build passed.
- Web: formatting passed, 328 contract tests passed, all four locale audits passed, production build passed.
- Repository policy and Ruff checks passed.
- The complete backend suite is delegated to the pull-request PostgreSQL gate. A root-directory run was invalid because migration tests could not resolve the Core `alembic.ini`; a parallelized Core run was also invalid because concurrent full-profile initialization exceeded the deliberately bounded job lease. Both invocation artifacts were excluded from acceptance evidence. All affected tests pass in the supported serial mode.
