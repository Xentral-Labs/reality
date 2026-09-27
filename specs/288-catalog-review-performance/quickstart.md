# Validation Quickstart: Shared Runtime Catalog

## Prerequisites

- Python 3.12 development environment installed for `packages/reality-core`.
- Local PostgreSQL test service available using the repository test configuration.
- Run commands from the repository root unless a command changes directory explicitly.

## 1. Specification and formatting

```bash
make spec-check
git diff --check
```

Expected: both commands exit successfully.

## 2. Central catalog contract

```bash
.venv/bin/pytest -q packages/reality-core/tests/test_application_catalog.py
```

Expected: successful reuse, copy isolation, concurrent single initialization, failure retry,
explicit clearing and fresh-build independence all pass.

## 3. Runtime consumer and adapter parity

```bash
.venv/bin/pytest -q \
  packages/reality-core/tests/test_proposal_review_parity.py \
  packages/reality-core/tests/test_capability_guidance.py \
  packages/reality-core/tests/test_http_boundary.py \
  packages/reality-core/tests/test_ai_mcp.py
```

Expected: Proposal Review, capability guidance, HTTP and MCP behavior remain unchanged, tenant
boundaries remain enforced, and migrated consumers reuse the central snapshot.

## 4. Production caller inventory

```bash
rg -n "load_application_catalog\\(" packages/reality-core/src/reality -g '*.py'
```

Expected: the canonical runtime snapshot initializer is the only production runtime call to the raw
builder. Any other result is documented as an explicit fresh-build path before completion.

## 5. Proposal Review performance

```bash
.venv/bin/python -m reality.benchmarks.proposal_review \
  --tenant TENANT_ID \
  --proposal PROPOSAL_ID \
  --runs 20
```

Expected: the script reports one successful runtime catalog initialization, 20 completed warmed
reads, and p95 service execution at or below 200 ms. Browser rendering and network transport are
not part of this measurement.

Observed on 2026-09-27 against the local PostgreSQL development database: 20/20 reads completed;
durations ranged from 4.06 ms to 8.82 ms and p95 was 8.30 ms. The pre-change profiled service read
was approximately 1.54 seconds, including 1.43 seconds of repeated catalog construction.

Live browser verification on 2026-09-27 used a freshly rebuilt development stack rebased onto
`main`. After restarting only the API process, opening an uncached proposal issued exactly one
`GET /api/tenants/{tenant}/change-proposals/{proposal}/review` request, returned HTTP 200 in
196 ms, and opened the review dialog in Chat without route navigation. A subsequent proposal read
under concurrent background polling completed in 453 ms; this transport-level observation includes
browser, proxy, database scheduling, and concurrent local development traffic and is not the
service-level acceptance metric.

## 6. Required backend suite

```bash
make lint
make test
```

Expected: all required repository checks pass with no schema or migration changes.

Focused verification after rebasing onto `main`: 132 passed and 2 skipped across the catalog,
Proposal Review, application tool, HTTP, MCP, capability guidance, and benchmark test modules.
