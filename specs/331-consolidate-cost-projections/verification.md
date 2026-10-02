# Verification: consolidated cost projections

Date: 2026-10-02. Scope: spec 316; subsequent acceptance also includes spec 319. No production database was migrated.

Current status: T015 is closed by the subsequent complete acceptance coverage of the
frozen specs 316/319 source scope. See [spec 319 verification](../332-integrate-account-defaults/verification.md)
for the final dedicated-server results, corrected snapshot documentation gate and
passing serial benchmark. Earlier results below are preserved as historical evidence.

## Design and review

The approved change replaces thirteen disposable cost-output tables with four typed
physical storage tables and thirteen writable compatibility views: nine fewer physical
tables. Input authorities and Source → Evidence → Reality records remain unchanged.
No command, service, tool or business-resource vocabulary changes.

Specification analysis covered all eight functional and five design requirements;
no critical findings remained before implementation. Final independent read-only
review found no actionable blocker in tenant/family identity, typed references,
null uniqueness, lifecycle guards, migration locking, copy parity or rollback.

## Executed checks

- Initial storage tests failed before implementation, proving the missing shared schema.
- Focused cost/publication and older-version rollback regression run: 29 passed.
- Shared-storage contract run: eight tests passed, including writable-view service
  results, cross-tenant/wrong-family rejection, immutable identities, stable indexes,
  idempotent/partial schema creation and repair of a missing lifecycle trigger.
- Final populated migration round-trip: one passed. Exact original columns, values,
  IDs, nullability, defaults, primary keys, checks, unique keys, foreign keys and indexes
  are restored at revision 0108. Equal IDs from separate old families remain distinct.
  Retained cost inputs and Source/Evidence/Reality authorities are unchanged across
  upgrade, downgrade and re-upgrade. Sealed shared-output mutation is rejected.
- Index regression rerun: three passed, including downgrade to revision 0058
  and re-upgrade. The full run exposed a historical index-inventory assertion
  that omitted the four new later-migration storage tables; its expected later
  table inventory was updated. Frozen shared-index parity remains independently
  covered, including a fresh interpreter.
- `make lint`, `make spec-check` and `git diff --check`: passed.
- `make docs-catalog-check`: passed; generated catalog vocabulary is unchanged.
- `make docs-build`: passed (14 Python reference tests and 112 Node tests).
- `make web-build`: passed (451 Node tests, TypeScript/Vite build and all four
  i18n catalogs complete at 2492/2492 keys).
- Complete backend suite: 5323 passed, 10 skipped, four failed, one warning
  in 2703.77 seconds (45:03). The index assertion failure was corrected and its
  complete three-test module passed on rerun. Remaining full-run failures:
  The demo settlement batching test failed with 10 invoices/0 payments instead of
  11 invoices/11 payments. An isolated rerun failed identically, and a temporary
  unchanged HEAD checkout reproduced the same failure (57.17 seconds). This is an
  existing failure outside spec 316; the full-suite gate was not marked complete at that stage.
  The full run also reported a demo execution profile scheduler timeout; its
  isolated rerun passed (119.42 seconds); the unchanged HEAD run also passed
  (118.07 seconds). A demo profile history test reported the same seed timeout
  in the parallel full run; its isolated rerun passed (72.35 seconds).

Tests use isolated temporary PostgreSQL databases. The complete backend run uses
four workers; shared-schema refinements and the index-inventory test update after
worker startup are covered by the final focused tests. At that stage the complete backend acceptance task was left unchecked; the subsequent acceptance below closes it.

## Migration evidence and limits

Migration 0109 locks original logical interfaces before copying. Bidirectional EXCEPT
checks compare every legacy column before retirement. Frozen migration DDL does not
import live ORM definitions. Rollback restores original UNIQUE/FK relationships before
adding primary keys, preserving compatibility with older primary-key migrations.

Compatibility views retain the original business grain and names; internal routing
columns are absent from ORM business fields. This reduces physical storage, not the
number of logical inspection resources. Generic settings and retained cost-input
consolidation are outside this approved slice.

## Original disposition before subsequent acceptance

Implementation, focused regression, populated migration, index, web and documentation
checks are complete. T015 was left open after that run because the complete backend result was red. The
existing demo settlement failure and the two parallel-only seeding timeouts prevent an
unqualified full-suite acceptance claim. No unrelated demo behavior was changed.
No deployment, live database migration or commit was performed.

## Subsequent acceptance

All runtime cases, including the earlier demo failures and timeouts, passed in the
final isolated dedicated-server run (5334 passes, ten skips, one snapshot-documentation
error). The copied coverage matrix was completed from the existing approved documents;
the full spec-policy module and unchanged serial replay benchmark then passed (24 tests).
Together these runs cover all 5336 unique non-skipped backend cases with passing evidence.
No runtime source or assertion changed between them. The final lint/spec/diff gates pass.
T015 is closed; earlier red-run counts are not rewritten. No production migration,
deployment or commit was performed.

## Current-main PR integration

Historical evidence above used local spec 316 and the former migration numbering.
The PR renumbers this feature to 328 and appends its migration after main 0114.
Combined current-main acceptance is recorded in spec 327 verification and hosted CI.

Combined current-main acceptance: PR #299, 5,564 backend cases passed, 10 skipped,
all 24 hosted gates passed. See spec 327 verification/ci-acceptance evidence; historical
local logs above retain their original source scope and former numbering.
