# Quickstart: Validate Demo Entrypoint Equivalence

## Prerequisites

- Local PostgreSQL test service is running.
- Core and Product Web dependencies are installed.
- Run backend commands from `packages/reality-core`.

## Canonical three-entrypoint proof

```bash
pytest -q tests/test_demo_entrypoint_parity.py tests/test_cli.py tests/test_user_access.py
```

Expected: interactive CLI, CLI auto, and authenticated Web/API runs produce equal
categorized manifests; cancellation, empty-company, populated/rerun, and tenant cases pass.

## Product Web contract

```bash
cd apps/web
node --test scripts/demo-entrypoint-contract.test.mjs
npm run test:i18n
npm run build
```

Expected: actual onboarding exposes separate empty/demo actions, gates the demo request,
sends the correct input, opens the returned tenant, and contains no demo business steps.

## Complete gates

```bash
make lint
make test
make spec-check
make web-build
git diff --check
```

Expected: all gates pass and no model or migration change exists.

## Manual review

1. Open Product Web as an approved user with no company.
2. Create an empty company and confirm no sample business records appear.
3. With a user having no company, choose the guided demo and cancel once.
4. Confirm the demo, open the tenant, and inspect SourceRecord, Document/Line,
   Commitments, Reservation, opening Movement, and derived inventory.
5. Compare the business outcome with `reality demo --auto`, ignoring presentation.

Only after executable evidence and final owner approval may `015/FR-010` be marked
verified and its accepted-gap row removed.

## Implementation evidence

- Manifest version: `guided-demo-v1`; six sections cover reference data, Source,
  Evidence, Reality, derived state, and explanation.
- Inventoried result: 3 parties, 1 item, 1 location, 1 source record, 1 source
  stream, 1 import job, 1 document, 1 document line, 2 commitments, 1 reservation,
  1 movement, 0 facts, 12 business events, 1 chat session, 2 chat messages, and
  0 ledger entries.
- Real interactive CLI, CLI `--auto`, and authenticated Web/API manifests are equal.
- Focused backend regression: 21 passed. Ownership and partial-failure subset:
  8 passed.
- Complete PostgreSQL backend suite on the isolated current-main branch: 243 passed,
  7 skipped.
- Product Web localization and contract suite: 18 passed. Production build passed
  with the pre-existing chunk-size advisory only.
- Ruff and `git diff --check` passed after implementation cleanup.
- No model or migration was added or changed for this feature. Existing CLI and
  shared `ensure_demo` behavior required no correction; the Web adapter delegates to
  that operation. Foreign-company lookup was aligned to the existing not-found
  boundary and covered by the complete suite.
- Product-owner final review was approved on 2026-09-02. `015/FR-010` is now
  `Verified as-is`; only that accepted-gap row was removed. Both `016/FR-006` and
  `016/FR-015` remain documented gaps.
- Final closure gates: repository Spec policy passed; focused Spec-policy and demo
  traceability tests passed (16 passed); `git diff --check` passed.
