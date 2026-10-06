# Verification: Essential intake completeness

## Test-first evidence

The focused pre-implementation regression run produced 25 expected failures and 4 passing controls (40 deselected). It demonstrated guessed currency/bank defaults, zero for an omitted price, missing review gaps, undated simulator/file orders and unsupported sales units. The source/no-effect assertions form part of each relevant acceptance test.

Final review added a failing proof for two timezone representations of one instant. Header consistency now compares parsed dates/UTC instants while keeping original row payloads unchanged.

## Local gates

- Spec policy, Ruff and business annotations: passed; 650 described functions, 115 described tests, no remaining required annotations.
- Frontend translations: 463 tests passed; all four locale audits passed.
- TypeScript and production web build: passed.
- Product documentation generation, reference tests, formatting, contract tests and production build: passed; generated vocabulary remains current.
- Browser acceptance: passed; 16 localized responsive reviews, missing price, exact approval, reload/edit/reject and response-loss recovery.
- Affected final regressions before the date refinement: 134 passed, 1 browser-dependent skip in 42.56 seconds.
- A redundant local full run was stopped after 502 passed and 4 skips; the complete GitHub PostgreSQL shards are the full-suite completion gate.

- Date/header and artifact regression matrix after refinement: 53 passed in 24.30 seconds.
- New admission and all affected historical stock/analysis/MCP reader suites: 318 passed in 118.60 seconds. Historical fixtures use explicit source/evidence/commitment service writers; new-admission refusals remain exercised directly.

## Complete PR verification

The required GitHub Quality gates run on the PR's current head: all four PostgreSQL shards, backend aggregate, frontend, seven fixture-browser shards, eight real-backend browser journeys, documentation and Spec policy. The first full run passed both unaffected PostgreSQL shards and all browser/frontend/docs gates; its 17 reader-fixture failures were repaired and covered by the 318-test local run. The final current-head full run remains the completion gate; its actual results will be recorded after completion.

## Review and rollout

The final diff is bounded to spec 379 and its contracts. No schema, historical repair, source mutation or new authority. Spec 301 explicitly records the replacement of its permissive sales-unit control; purchase conversion remains unchanged. Original inputs remain retained when essential financial statements refuse preparation. This PR is not merged by the implementation task.
