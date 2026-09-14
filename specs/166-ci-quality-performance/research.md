# Research: Faster Quality Gates

## Decisions

### Use a repository-owned path classifier

The existing site gate performs an inline diff. A small standard-library classifier is
more directly testable and avoids a third-party Action. It defaults to running backend
quality when it receives no paths or an unsupported scope.

### Use two runner shards with two workers each

The previous job used `pytest -n 2 --dist loadscope`. A measured four-worker GitHub run
finished in 10:36, only 25 seconds faster than the 11:01 baseline, showing that one
runner is CPU/I/O constrained. Two independent runner shards provide separate CPU and
PostgreSQL services while retaining two workers per runner. A deterministic greedy
file-size allocation covers every test file once and approximately balances work.
Each xdist worker still creates a random `reality_pytest_*` database, and tests requiring
committed state create random `reality_migration_*` databases.

### Keep the full suite on main

Pull-request path filtering improves feedback without weakening the integrated branch.
Every push to `main` retains the complete backend suite, catching integration effects
and validating the classifier after merge.

## Baseline

PR #189 run 34500256530: backend-quality 11:01 total; PostgreSQL suite 10:19;
installation 0:17; service initialization 0:11.
