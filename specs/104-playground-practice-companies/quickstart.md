# Verification
## Shared App access evidence — 2026-09-07

FR-008/009: observed missing-bootstrap and denied-operation regressions before
implementation. Final API/master boundary suite: 69 passed. Covers normal item writes,
shared source/document/commitment/movement/ledger services and Simulator reads;
temporary, archived, unverified, removed-member and foreign-admin exclusion; external,
unknown and destructive-operation denial. App cannot directly execute a Playground
proposal; the original confirmation still succeeds. Full backend run: 1380 passed,
7 skipped; subsequent confirmation-boundary additions covered by the 69-test run.
Web: 107 contracts, build, 1195 keys in four languages, formatting, Ruff, spec and
whitespace checks pass. Isolated practice browser completes prior workflows then
opens the exact tenant in the normal App, sees the existing document and both company
choices, and verifies the run backlink and Sandbox banner without extra writes.
Screenshot inspected. Local API/web rebuilt; API container reports healthy. No schema,
purpose conversion, production simulation access or user-data mutation performed.
Normal business rows retain their bootstrap shape and remain preferred defaults;
existing named practice companies become eligible from persisted owner/run state.

Create named A, quick experiment, named B, replace quick experiment. Reopen A and B:
same IDs/references, writable, own-company name correct; no shared stock.
Retry with the same key, then changed name/kind: same input is idempotent, changed
payload conflicts. Test another owner, invalid names and practice restart refusal.
Run full PostgreSQL, migration, Ruff, spec policy, web contracts/audit/build and browser
journeys before local deployment. Never delete user data.

## Evidence — 2026-09-07
- Initial service proof: 6 failed, 1 passed before implementation (unknown parameters).
- Full PostgreSQL suite: 1361 passed, 7 skipped; two assertions still expected the old
  migration head. Updated head expectations; final service/migration run: 18 passed.
- Web: 103 contracts, 1150/1150 strings in four languages, formatting and build pass.
- Isolated browser: named company setup, cancelled setup, lost response/reload/retry
  with same key/name/kind, saved reopen, no company archive warning, full guided story,
  both themes and mobile cockpit pass. Ordinary quick and free-operation stories pass.
  Browser fixtures do not mutate a user's tenant. Named setup screenshot inspected.
- Ruff, spec policy and whitespace pass. No extension hooks configured.
- Local database upgraded to 0043_practice_companies; API healthy, web serves
  index-DoGMlBLw.js. Existing sandbox readable with temporary default and original
  references. No deletion, production link or user-account sample creation performed.
- Review: company name reused from Tenant; only lifecycle discriminator added;
  owner locks/idempotency retained, practice restart refused. Remote migration 0042
  remains outside this branch; merge migration heads on later integration.

## UI refinement evidence — 2026-09-07
- FR-007: 54 Playground API tests pass, including canonical catalog parity and
  unauthenticated refusal (initial regression failed on missing route). 103 frontend
  contracts, 1161 translated UI strings, formatting, build, Ruff and spec policy pass.
  Browser verifies metadata rendering, search, error/retry, fresh reads on reopen,
  Escape dismissal and the full guided journey. Desktop/mobile dialog screenshots
  inspected. No data mutations or schema changes; descriptions remain canonical.
- FR-005/006: 103 web contracts pass, 1154 localized strings covered in all four
  languages, production build, formatting, spec policy and whitespace pass.
- Isolated quick/practice browser journeys pass: single setup heading, no review
  Refresh, visible outlined Cancel at desktop/mobile in both themes, no writes on
  cancellation; missing shipment explanation and back; recorded-step exit notice,
  continue and actual return to operations without added writes. Practice journey
  also verifies lost setup response/retry. Screenshots inspected.
- Scope is UI only; existing service/API/persistence and execution guards unchanged.
  No new backend migration or data mutation required. No extension hooks configured.
