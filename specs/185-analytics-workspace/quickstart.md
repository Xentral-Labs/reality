# Analytics verification quickstart

This is the planned validation guide. New commands/files below become runnable during implementation; none is claimed implemented or passing by this document.

## Prerequisites

Use the repository's Python virtual environment, installed Web dependencies, local PostgreSQL test admin endpoint and normal migration procedure. Persistence tests create isolated temporary databases through `tests/conftest.py`; never point them at a company database. Recheck Alembic heads before assigning a migration revision.

## Agent flow

1. Discover with `analytics_catalog`.
2. Resolve a real product ID using existing `business_records_discover`.
3. Execute the JSON definition in `contracts/agent-tools.md`, replacing the illustrative ID and using matching fixture dates.
4. Change dimensions to weekly product grouping and compare with the preceding period. Values must be exact and currencies/units separated.
5. Fetch contributors for one group; inspect its underlying order/line/source.
6. Open the definition in Reports, change a filter and Run. Discuss passes it back to the same chat.
7. Save through authenticated Web/chat; verify confirmation for agent changes. A tenant-only MCP token must execute queries but refuse private report access.

## CLI flow

After implementation, `reality analytics catalog` describes capabilities. Save only the definition object from the contract example to a JSON file, then run `reality analytics query --file definition.json`. For contributors use the complete request object in its own file. Export with `reality analytics export --file definition.json --output result.csv`. These commands call the same application tools as Web/MCP; no raw SQL interface is introduced.

## Tests first

Planned focused command:

```sh
cd packages/reality-core
../../.venv/bin/pytest tests/test_analytics_definitions.py tests/test_analytics_questions.py tests/test_analytics_execution.py tests/test_analytics_contributors.py tests/test_analytics_reports.py tests/test_analytics_exports.py tests/test_analytics_adapters.py tests/test_analytics_chat.py
```

Coverage must contain all Q01–Q30 cases, with explicit restricted outcomes. Use dates around ISO year/DST boundaries, multiple currencies, repeated order lines, partial billing/payment and movement corrections. Existing canonical tests remain required; passing a new isolated tool test is insufficient.

## Browser review

Use the normal authenticated Web setup. Existing Home links still reach Overview. Build the customer/product/week question in Explore; verify draft/result separation, stale-request cancellation, table/chart/pivot values, Inspector navigation, private save/reopen/revision recovery/export and chat handoff. Repeat critical flows at 390px and 1440px in all four languages, with keyboard access. Screenshot review covers chart labels, table overflow, error/empty states and the existing open chat dock.

Planned browser runner: `node apps/web/scripts/analytics-browser.mjs`, using the repository's existing Playwright environment conventions. Also run current workspace and shell/chat regression scripts. Browser fixtures prove interaction; PostgreSQL tests prove business values.

## Required completion gates

```sh
make spec-check
make lint
make test
make web-build
make site-build
make docs-generate
make docs-catalog-check
make docs-build
```

Run `npm run i18n:audit` and `npm run test:contracts` in `apps/web`. Record benchmark environment, input seed, EXPLAIN evidence, query list, cold/warm latency and p95 for 100,000 order lines using `benchmarks/analytics/run.py`. The first implementation must add that runner and its documented invocation. No new index is accepted based on speculation alone.

Record results in the feature's verification evidence. Failed gates and unimplemented tasks stay visibly open. No deployment, merge or production mutation is part of this validation guide.
