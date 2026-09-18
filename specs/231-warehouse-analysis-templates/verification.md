# Verification evidence

## Review
The owner approved warehouse measures and matching templates. No migration, new
business mutation or persisted stock state was added. core.inventory_rows remains
the only stock derivation used by the graph. A fixed two-entry registry extends the
existing finance adapter without making arbitrary services callable.

Reviewed boundaries: current per-article/all-location grain; exact quantities;
active reservations only; availability can be negative and is not release permission;
unit, tenant, snapshot and fanout guards retained. Input bounds are 20,000 articles
or open supplier commitments, 100,000 movements or commitment revisions. The stricter
commitment bound also stays below PostgreSQL's bulk parameter ceiling. No truncation.

## Automated verification
- Final focused warehouse/finance suite: 19 passed (11 warehouse, 8 finance), including
  service/Register parity, reservation release/consumption, internal transfer, movement
  correction, negative/zero stock, tenants, units, snapshot/fanout refusal, all input
  bounds, constant read count, six templates and chat compilation.
- Web contracts: 266 passed; production build, format check and all four languages'
  i18n audit passed. Existing Vite large-chunk advisory remains.
- Ruff, specification policy and whitespace checks passed.
- Catalog generator completed via its underlying Python command; make is unavailable
  because of this machine's Xcode license setup.

## Native Chrome review
Catalog shows 58 objects / 183 relationships / 351 fields. Current article stock loads
real preview data with the explicit availability explanation. All six new starting
questions appear in Use a template. Stock by article opens the existing unsaved builder
and returns 16 article rows with physical/reserved/available quantities and unit axes.
Existing question frame and shared table styling remain. No report was saved, no chat
message sent and no business mutation performed.

## Full backend suite
Full backend suite: **2,857 passed, 9 skipped**, 588.83 seconds. One pre-existing
SQLAlchemy transaction-cleanup warning in the storyline API test. Log:
`/tmp/reality-warehouse-full.log`. The final stricter commitment bound and its additional
regression were also verified in the 19-test focused suite after full-suite collection.

All FR-001–004 checks and implementation tasks are complete locally on main. Existing
spec228–230 work is preserved. No commit, push or deployment was performed.
