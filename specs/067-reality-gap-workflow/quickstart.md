# Quickstart: Reality Gap Workflow

1. Ask Chat which orders are express and capture the unsupported answer.
2. Open the same gap in Web and MCP; verify identity/state parity.
3. Add purpose, workaround, recurrence, desired use, SourceRecords, and path.
4. Request a Fact recommendation; verify no Fact or rule changes.
5. Verify a member cannot classify/activate; an owner can accept and prepare.
6. Simulate matching, invalid, absent, and ambiguous sources.
7. Confirm activation; ingest a matching source and verify one traceable Fact/outcome.
8. Confirm replay twice; verify no duplicate Facts.
9. Disable; verify future sources stop while historical Facts remain.
10. Classify typed Reality; verify a developer package and no runtime change.
11. Verify foreign and stale actions fail closed.

Required gates:

```bash
make spec-check
make lint
make test
make web-build
cd apps/web && npm run i18n:audit
```

Expected: the customer operates Open questions through all three surfaces; only a closed Fact rule executes in user space, and broader changes stop at developer handoff.

## Verification evidence (2026-09-04)

- Spec policy: PASS (`make spec-check`).
- Python lint: PASS (`make lint`).
- Full backend suite: PASS, 406 passed and 7 skipped (`make test`).
- Focused feature/MCP/catalog/migration/tenant suite: PASS, 66 passed and 2 skipped.
- Web contract suite: PASS, 75 passed.
- Web production build: PASS; the existing Vite large-chunk advisory remains non-blocking.
- Localization audit: PASS for English, German, Dutch, and Spanish (872/872 keys each).
- Guided-capture Web contract: PASS; the first step explains the effect and the four-step flow keeps technical terms after capture.
- Updated Web contract suite: PASS, 76 passed; localization audit PASS at 899/899 keys per language; production build PASS.

The automated verification covers persistence, migration rollback, tenant boundaries,
proposal transport, deterministic Fact creation, replay safety, catalog drift, and Web
route/build contracts. Manual responsive visual review and the large-volume benchmark
remain explicitly open in `tasks.md`.

## ERP-ready conditional rule acceptance (2026-09-04)

1. Create an order rule with `all` conditions for a high value and unpaid status, a constant Boolean output, and a Commitment subject.
2. Simulate one matching source, one normal condition miss, one missing field, one wrong type, and one ambiguous subject. Verify that only the match predicts a Fact and every category is distinct.
3. Activate through confirmed Chat or MCP mutation, import matching and non-matching immutable SourceRecords, and verify service/Web parity plus exact rule-version provenance.
4. Create a line rule with one bounded `line_items` iteration, relative conditions and output path, and the DocumentLine resolver. Verify exact per-element mapping and no human-number identity.
5. Verify received time and timezone-aware source-path observation time, including refusal of naive or invalid timestamps.
6. Activate a competing rule family and verify an incompatible value becomes a visible conflict with no silently preferred Fact.
7. Replay more than one page, stop, resume with the opaque cursor, retry the final page, and verify identical cumulative totals with no duplicate Fact or outcome.
8. Inspect the rule summary through application tool, MCP, HTTP, and Web; verify version, last evaluation, outcome counts, bounded failures, replay progress, Fact links, and SourceRecord links.

Automated acceptance evidence:

- Closed all-of conditions cover equality, inequality, membership, existence, and ordered comparisons with typed operands; rules reject unsupported operators and more than 20 conditions.
- Constant and source-path output, timezone-aware source timestamps, normal `not_applicable` results, invalid values, Commitment targets, DocumentLine targets, and the 500-element line bound are covered by 23 focused rule tests.
- The checked-in Shopify gift-wrap fixtures produce one prospective/created Fact for `true` and one normal non-applicable outcome for `false` in both simulation and replay.
- Competing values become visible conflicts and create no silently preferred Fact.
- Scope-bound opaque cursors reject malformed or broadened requests, resume deterministic 500-source pages, and remain retry-safe.
- The PostgreSQL acceptance benchmark passed with 10,000 gaps plus 100,000 entries under the two-second first-page target, and 10,000-source replay completed in 20 pages under the 60-second target with exactly 10,000 unique outcomes.
- Rule detail exposes immutable version configuration, last evaluation, outcome counts, bounded failure examples, generated Fact IDs, and SourceRecord IDs through the shared service, HTTP client, MCP schema, and Web UI.
- Manual and rule-created Facts use one canonical persistence primitive; rule evaluation participates in its caller's transaction and retains exact rule-version provenance.

Release gates:

- `make spec-check`: PASS.
- `make lint`: PASS.
- `make test`: PASS, 434 passed and 7 skipped; the focused rule suite contains 23 tests.
- Migration upgrade/downgrade suite: PASS, 7 tests.
- `make web-build`: PASS, 78 contracts and 999/999 localized keys in English, German, Dutch, and Spanish; the existing Vite chunk-size advisory remains non-blocking.
- `make site-build`: PASS, 48 tests and all four 424-key catalogs.
- `make docs-build`: PASS, 37 tests and production render.
- `git diff --check`: PASS.

Final Constitution review found no exception: sources remain immutable and lossless,
Facts retain SourceRecord and exact rule-version links, DocumentLine resolution uses
opaque source-line coordinates, every query is tenant scoped, adapters delegate to the
shared service, and unsupported model changes still stop at a developer package.

Manual desktop/mobile visual review remains open as T038/T084 because the in-app browser
runtime reported that no browser was available in this session. It must be completed
before merging; no automated result is being presented as visual approval.

## Bounded ALL/ANY group acceptance (2026-09-04)

- A reviewed rule now represents `B2B AND (high value OR overdue)` as explicit nested groups; no expression text is parsed or executed.
- The evaluator accepts at most three group levels and 20 leaf conditions and rejects unsupported modes, empty nested groups, excess depth, and excess leaves before storage.
- Existing flat conditions retain their top-level all-of behavior and immutable rule-version history.
- Three-valued evaluation is order-independent: `ANY` succeeds when one branch is true even if another required path is unknown; it reports invalid input only when no branch is true. `ALL` symmetrically reports a normal non-match when one branch is false.
- Simulation and replay truth-table coverage passes with only the exact matching SourceRecords producing Facts.
- Focused backend service/tool/API suite: PASS, 32 tests.
- Complete rule suite: PASS, 29 tests.
- Web contracts: PASS, 78 tests; localization audit: PASS, 1005/1005 keys in all four languages; formatting and production build: PASS.
- Spec policy and Python lint: PASS.
- Live MCP HTTP acceptance: PASS. A temporary authenticated MCP client proposed and confirmed one nested rule, activated it, imported four Shopify orders through `source_record_ingest_propose`, and processed their queued imports. Exactly the two expected orders (`B2B AND (high value OR overdue)`) produced Facts; the other two produced none. The test then disabled the rule and revoked its temporary MCP token. Immutable test sources, proposal receipts, outcomes, and Facts remain as audit evidence in the Acme Bikes tenant.
