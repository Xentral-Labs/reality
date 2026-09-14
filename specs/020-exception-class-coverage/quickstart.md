# Validation Quickstart: Complete Operational Exception Coverage

## Prerequisites

- Python 3.12+ development environment
- Local PostgreSQL test service
- Approved Spec 020 taxonomy and shared exception service

## 1. Validate Taxonomy Drift

Run the focused coverage tests. The production taxonomy must map exactly five visible
classes, the nested `insufficient_reservation` cause, every derivation registry key, and
focused evidence. Controlled missing, stale, duplicate, and unproven fixtures must fail
and name every mismatch deterministically.

## 2. Run the Multi-Class Story

Build both populated tenants with overlapping human identifiers and distinct opaque IDs.
Use a controlled UTC instant. Create every approved condition and verify exactly five
local visible identities. The outgoing-risk row must carry
`insufficient_reservation` and no duplicate reservation row may exist.

## 3. Prove Each Class

- Partially reserve and fully reserve/ship outgoing demand.
- Compare overdue, equal-time, future, missing-date, partial-receipt, and full-receipt supply.
- Fail and successfully retry source interpretation while preserving raw Source.
- Compare unlinked shipment/receipt/return with linked execution, opening, transfer, and adjustment.
- Compare unmatched, partially allocated, and fully allocated customer/supplier payments.

For each class verify positive, negative, foreign-tenant, explanation, and clearing proof
where an owning remediation exists.

## 4. Prove Shared Interfaces

Compare direct service results with the rebuilt exception projection, application tool,
Web/API list and Inspector, MCP list/explain, and fallback Chat routing. The class, cause,
record ID, causal values, and tenant outcome must agree. Presentation adapters must not
contain class predicates.

## 5. Run Repository Gates

```bash
python3 scripts/check_spec_policy.py
.venv/bin/ruff check <changed-python-files>
cd packages/reality-core
TEST_POSTGRES_DATABASE_URL=postgresql+psycopg://reality:local-only@localhost:54329/reality_test ../../.venv/bin/pytest -q
```

Expect focused and complete PostgreSQL suites to pass. No migration or frontend change
is planned.

## 6. Close the Baseline Gap Last

After all derivation, taxonomy, explanation, adapter, tenant, full-suite, policy, and
owner-review gates pass, change only `013/FR-005` to `Verified as-is`. Remove only that
row from `docs/SPEC_COVERAGE_MATRIX.md`, update the `013` and accepted-gap counts from
9 to 8, and preserve every unrelated decision. Record exact counts, commands, defects,
and approval here during implementation.

## Implementation Evidence — 2026-08-31

- Focused exception service and taxonomy: `13 passed`, then `26 passed` after enabling
  executable evidence resolution in the normal application catalog gate.
- Shared service plus Projection, application tool, Web/API, Inspector, and MCP slice:
  `49 passed, 2 skipped`.
- Complete backend PostgreSQL suite: initially `189 passed, 7 skipped`; after final
  registry review and remediation, `190 passed, 7 skipped` in 10.27 seconds. The skips
  are existing environment/optional integration cases and are not sole Spec 020 proof.
- Spec policy: `Spec policy passed`; focused policy regression: `8 passed`.
- Ruff: all changed Python files passed.
- Frontend: production build passed. Vite reported only its existing advisory for a
  JavaScript chunk larger than 500 kB.
- Translation audit: `en`, `de`, `nl`, and `es` each passed `775/775`, with zero missing
  or invalid entries. All 9 localization contract tests passed.
- No model or Alembic file changed. No schema or persisted exception lifecycle was added.
- MCP required no server change: its existing thin application-tool adapter propagated
  the shared list/explain contract and passed the adapter slice.
- Initial full-suite defect: six catalog evidence paths incorrectly repeated the
  `packages/reality-core/` root, producing 14 deterministic catalog failures. The paths were corrected
  to the resolver's backend-relative convention; the focused gate and full suite then
  passed.
- Final-review defect: catalog keys were validated, but runtime assembly still called
  derivators directly and two classes shared one Commitment derivator. Runtime assembly
  now iterates the validated five-entry registry, with one derivator per visible class;
  the renewed exception/adapter slice passed `67 passed, 2 skipped`.
- Current taxonomy evidence: five visible class identities and one nested
  `insufficient_reservation` cause. Accepted baseline gaps changed only from 9 to 8 by
  verifying `013/FR-005` through Spec 020.
- The owner approved the implementation and final review on 2026-08-31. All 52 tasks and
  requirement-coverage rows are closed. Commit and pull request remain separate gates.
- After PR creation, current `main` introduced the approved Spec 021 deployable-app
  layout. `origin/main` was merged, all Spec 020 code/tests/evidence were moved from
  `backend/` to `packages/reality-core/`, and Web commands now run from `apps/web/`.
  The post-merge backend suite passed `195 passed, 7 skipped` in 10.07 seconds; the Web
  build, four-language `775/775` audit, and 9 localization tests also passed. The only
  build notice remains Vite's advisory for a JavaScript chunk larger than 500 kB.
