# Plan: Complete unified business journey
**Language**: English
## Technical context
Python/pytest, existing PostgreSQL fixture and SQLAlchemy/Alembic; real Uvicorn API and separate Vite app; existing Playwright/Chrome tooling. No dependency or schema changes.
## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Provenance | Assert original source and shortest order/invoice/credit/settlement links | PASS |
| Reality | Assert derived stock, reservations and open amounts | PASS |
| Schema | No schema changes; disposable database runs current migrations | PASS |
| Tenant/services | Service-created business seed; real ordinary owner login and existing API tools | PASS |
| Test-first | Full journey tests expose defects before bounded fixes | PASS |
| Explainability | Inspect actual resulting evidence and before/after review | PASS |
| Received values | Stated order1000, invoice400, credit200 and refund75 supplied independently | PASS |
| Simplicity | Dedicated pytest browser runner reuses existing database cleanup and browser locators | PASS |
## Design and files
- packages/reality-core/tests/test_unified_business_journey.py: shared-tool business story, partial/full refund variants, no-effect review, replay, post-reversal history and source/evidence/reality assertions.
- packages/reality-core/tests/browser/unified_business_journey.py: explicitly invoked integration test, outside automatic test_ collection. Reuse postgres_database, migrate disposable DB, seed core business references/opening stock and test-only auth owner/membership. Own API/Vite subprocesses on separate ephemeral ports; actual browser login with auth enabled; clean up handles in finally. No shared process or database access.
- apps/web/scripts/unified-business-journey-browser.mjs: real UI actions and read-only API inspection. No synthetic financial responses. Capture real proposal IDs/receipts; review before confirmation, reload after it; follow persisted opaque links between steps. Save screenshots and result JSON to supplied artifact directory.
- Repair only proven defects in existing services/tools/read models or apps/web/src/unified components. Record each finding and applicable FR before edits. No general redesign or new domain policy.
## Test strategy
FR-001/002/003/004 and DR-001 in service story and real-browser journey. FR-005 in reproducing journey plus focused regression for each defect. DR-002 through unique database, ordinary owner, real HTTP and deterministic subprocess cleanup. Run complete backend suite after source/test freeze, web build/contracts/i18n/format and affected adjacent browsers, root lint/spec/diff checks.
## Risks and rollback
Seed transactions must commit before separate API reads. Avoid inherited bootstrap/demo environment and shared URLs. Use strict ports, readiness deadlines, bounded browser execution and finally cleanup. Retain failure logs/screenshots. Identity ORM setup is test scaffolding; operational business setup and actions use shared services. Revert bounded fixes independently; test harness has no product runtime effect. No migration rollback required.
