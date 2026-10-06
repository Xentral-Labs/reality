# Verification: Essential intake completeness

## Test-first evidence

The focused pre-implementation regression run produced 25 expected failures and 4 passing controls (40 deselected). It demonstrated guessed currency/bank defaults, zero for an omitted price, missing review gaps, undated simulator/file orders and unsupported sales units. The source/no-effect assertions form part of each relevant acceptance test.

## Local gates

- Spec policy, Ruff and business annotations: passed; 650 described functions, 115 described tests, no remaining required annotations.
- Frontend translations: 463 tests passed; all four locale audits passed.
- TypeScript and production web build: passed.
- Product documentation generation, reference tests, formatting, contract tests and production build: passed; generated vocabulary remains current.
- Browser acceptance: passed; 16 localized responsive reviews, missing price, exact approval, reload/edit/reject and response-loss recovery.
- Complete PostgreSQL suite: running; no completion claim until required PR CI passes.

## Complete PR verification

The required GitHub Quality gates run on the PR's current head: all four PostgreSQL shards, backend aggregate, frontend, seven fixture-browser shards, four real-backend browser journeys, documentation and Spec policy. Current results will be recorded after completion.

## Review and rollout

The final diff is bounded to spec 379 and its contracts. No schema, historical repair, source mutation or new authority. Spec 301 explicitly records the replacement of its permissive sales-unit control; purchase conversion remains unchanged. Original inputs remain retained when essential financial statements refuse preparation. This PR is not merged by the implementation task.
