# Verification

## Pre-implementation review
Approved scope recorded in spec. Eight requirements mapped to tests and implementation; no ambiguities, duplications, unmapped tasks or critical findings. Constitution passes all eight principles. Built-in requirements checklist: 6/6 checked. No extension hooks configured. No migrations.

Initial failing proof: targeted tests failed collection because operational_previews did not exist (after allowing local PostgreSQL test access). Implementation verification pending.

## Approved extension review
The user's master-data request adds US4 and FR-009/FR-010. All ten requirements map to test and implementation tasks. Re-review found no unresolved clarifications or Constitution exceptions. The initial master-data regression failed on the missing `accounting_code` list field before implementation.

## Verification completed on 2026-09-16
- Targeted PostgreSQL suite: 30 passed, including operational previews, master-data names/fields, tenant isolation, source amounts, revised commitments, settlement/reversals, read-only behavior and unchanged edit revisions. Repeated against the isolated PR checkout with explicit `PYTHONPATH=src`: 30 passed.
- Isolated PR frontend: 194 tests passed; all four localization audits passed; production TypeScript/Vite build passed. Existing bundle-size advisory remains.
- Browser acceptance passed for desktop/mobile in four languages, keyboard disclosure, full explanation, all operational register families, all four master-data families and navigation placement. Browser requests were GET-only. Screenshots reviewed at `/private/tmp/reality-209-browser/` (local artifacts).
- Visual review caught horizontal-scroll clipping in master-data previews with the chat panel open. The shared scroll container now supplies its inline size, and sticky previews are bounded to that size. Browser assertions prove both preview edges remain visible.
- Ruff and specification policy passed in the shared workspace and isolated PR checkout. Generated catalog parity passed in the shared workspace; no catalog API signature changes.
- Full PostgreSQL suite: 2,618 passed, 9 skipped, 3 failed in 538.36s. All three failures were `handler_timeout` during demo-company seeding (`test_creation_answers_before_the_profile_is_seeded`, international-demo intake, seeded invoice settlement). Sequential rerun: all 3 passed in 21.26s. No production timeout or test threshold was changed. The failures occurred under concurrent verification load; this cause is inferred from the timeout traces and clean rerun. Thus every collected non-skipped test passed either in the full run or its targeted rerun; the original full run itself was not all-green.

## Change isolation
An isolated `feat/209-operational-previews` checkout includes only this feature. Existing chat, demo simulation and terminology changes in the user's working tree were preserved and excluded from the PR.

## Final review
No outstanding requirement, tenant-scope, source-authority or schema findings. Public financial service signatures and generated catalogs remain compatible. Optional Inspector preview content leaves full explanations intact; reference detail retains raw editing inputs and revision identity. All implementation and verification tasks are complete, with the full-run timeout/retry qualification above.
