# Verification checkpoint: explicit reviewed Shopify profiles

This checkpoint implements pure first-order, supported change and refund planning
through the shared explicit preparation/approval services. The automatic import
adapter and demo/bootstrap cutover are still pending. No acceptance story is marked
complete on the strength of preparation tests alone.

Observed PostgreSQL results before this checkpoint:

- Shared intake, Shopify and financial admission: 27 passed; includes failure-first
  changed-invocation regression, atomic rollback and retained receipt replay.
- Admission, file packaging, migrations, credit exposure and kits: 66 passed.
- Shopify, inspector presentation and manual document corrections: 27 passed;
  includes failure-first unknown-amount presentation and frozen unknown-item mapping.
- Nullable-amount migration upgrades/downgrades an empty schema and refuses a
  downgrade with source-unstated values without rewriting evidence.
- Frontend TypeScript/build, spec policy, Ruff and business annotation audit pass.
- Catalog outputs regenerated; catalog drift check requires the committed baseline.

Still required before full feature completion: automatic adapter and transport
cutover, legacy story updates with explicit reviewed decisions, real competing
approval/crash cases, all required repository gates and green PR checks. Bulk,
mandates and universal writer enforcement remain separate unfinished packages.

Follow-up verification: 39 admission, Shopify, financial and refusal-catalog tests
pass after an observed callback regression for an omitted commitment priority.
Canonical invocation checks now bind omitted optional values as well as explicit
arguments. The obsolete missing-line-amount refusal and its translations are
removed because null source evidence is now supported rather than rejected.
