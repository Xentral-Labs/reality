# Verification: Business analysis coverage

## Implemented scope
55 catalog objects, 178 declared relationships, 326 fields. Dedicated sales/purchase
and payment types, warehouse and supporting records, plus evidence/financial details.
Old invoice keys and model_version sales.1 retain meaning. No schema migration, business
writes, saved-report mutation, chat send, remote commit or deployment.

## Specification gates and review
Approved owner scope recorded before implementation. Six requirements map to ten tasks;
requirements checklist passes, no unresolved clarification or Constitution exception.
Cross-artifact analysis found no uncovered requirement or critical issue. Independent
read-only compiler/catalog review found parent scoping and reverse same-table joining
defects; regressions accompany both repairs. Final review found missing invoice-credit
and purchasing-commitment routes; populated tests failed before and passed after those
five additive edges. Generic document ship-to is labeled distinctly from partner.

## Tests and checks
- Reporting and guided-builder suite: 213 passed, including 30 expansion cases.
  `/tmp/reality-catalog-final-backend.log`, `/tmp/reality-catalog-evidence-tests.log`.
- Web contracts: 265 passed (`/tmp/reality-catalog-final-test-contracts.log`).
- TypeScript and production build: passed (`/tmp/reality-catalog-final-build.log`).
  Existing bundle-size advisory remains.
- Web formatting and four-language audit: passed (`/tmp/reality-catalog-final-*.log`).
- Complete backend Ruff check from packages/reality-core: passed.
- Spec policy and git whitespace checks: passed.
- Catalog reference generator: successful and idempotent against current working files;
  four generator unit tests passed. The git-diff catalog target is unsuitable for the
  already-uncommitted generated pages, so content hashes verify freshness instead.
- Full backend regression run: 2,833 passed, 9 skipped, one transaction-cleanup warning,
  in 636.88 seconds (`/tmp/reality-catalog-full-backend.log`). Final reporting run
  includes the subsequently added edge/evidence regressions: 213 passed.

New regression fixtures cover mixed document types, same human numbers, neighbor tenants,
malformed cross-tenant parent links, line roots and joins, observed vocabularies,
received negative amounts, fan-out refusal, actual purchase commitments, invoice-linked
credits, reverse return-resolution filtering, invalid parents, component header/line
ownership and previous source versions. All table nodes and structural edges execute
in PostgreSQL, including both directions and bounded recursive edges.

## Browser evidence
Native Chrome, existing local test company: grouped catalog/search, supplier invoice
selection and populated preview (three records), handoff to Builder with the same three
records, desktop and 390px mobile Builder/catalog. Restored desktop device mode and
closed DevTools. No report saved and no chat message sent. Visual review preceded the
last five relationship additions; those are verified by populated PostgreSQL tests.
Dark mode was not separately switched. Long labels have field counts on a second line.

## Remaining explicit boundaries
Derived availability, stock and aging continue through canonical operational views;
this change does not implement service-backed graph balance execution. Finance mapping
and assignment histories and full raw source payload inspection stay in the Inspector.
Campaign's pre-existing fact-backed example remains without supported preview fields.
Recorded document/credit amounts preserve their received sign and are not net revenue.
Historical shipping/fact/source rows are labeled accordingly. No claim of all possible
business calculations is made by the object count.

Final review: all ten tasks complete, no remaining failing required check. Changes remain uncommitted on main. Browser chat is visible again after returning to desktop.
