# Verification

Run make lint, make spec-check and make test. Focused cases: test_sandbox_read_parity.py and test_playground_api.py. Rebuild matching local services, verify port8080 Warehouse and other affected reads, then record results here.


## Focused evidence

Twenty new parametrized regression cases first failed with the exact ordinary-workspace rejection. After the scoped fix, the new cases plus existing reference and Playground HTTP suites passed: 94 tests. Test fixtures create a real ready Sandbox through company setup, never reclassify a persisted tenant. Warehouse values are checked with a database write observer; source filters, master-data details, proposal non-execution, original CSV bytes, preview, anonymous access and foreign records/owners are covered. Existing lifecycle and mutation cases stay green.

All remaining ordinary-workspace calls were reviewed: master-data preparation/confirmation and CSV staging/preparation only. Price-list reads and manual-document snapshots already use scoped reads. AI-settings reads can initialize/migrate credentials and are not ordinary business observations; secret resolution, external credentials and temporary lessons retain their existing policies.

The inherited duplicate spec154 directory was resolved by renaming register-empty-state documentation to spec156. Lint and spec policy pass in both isolated and integrated worktrees. No frontend, migration or database-purpose changes.


## Complete verification and local rollout

Isolated branch: 1,959 passed, 9 skipped (357.21 s). Integrated tree: 1,959 passed, 9 skipped and one documentation-path false positive; the phrase “backend/web” in a pre-existing coverage note was changed to “backend and web”, then all eight repository-layout tests passed. No application code changed after the complete run. Lint, spec policy and scoped diff review passed. Frontend code was unchanged.

Matching API, MCP, scheduler, worker and invitation-worker images were rebuilt and recreated with the existing root environment file; no migrations or data resets. API/MCP healthy, all five processes running with zero restarts, port8080 returns HTTP200.

Deployed service calls for the affected local demo ran in a PostgreSQL READ ONLY transaction: stock 16, reservations 4, movements 65 (50 on the page), customers 4, suppliers 3, items 16, locations 2, source systems 1 and source records 607 (50 on the page). Every master-data family also passed a detail lookup. This verifies actual stored data through the same services used by the API; authenticated HTTP behavior is covered by the route matrix. Browser interaction was not required.

Final review: seven read entrypoints now validate tenant existence; scoped queries, calculations, pagination, source bytes and existing mutation checks are unchanged. All ordinary-workspace callers remaining in runtime code are mutation entrypoints.

Review PR: https://github.com/Xentral-Labs/reality/pull/165. Local checks and rollout are complete; GitHub CI runs on the published head.

Hosted verification is blocked: GitHub run 34372650617 did not start its jobs because the account has failed payments or needs a higher spending limit. No test failure was reported by an executing runner. This requires account billing resolution before CI can validate the published head; no billing settings were changed.
