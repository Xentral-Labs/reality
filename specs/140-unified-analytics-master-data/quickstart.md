# Validation guide

Baseline: Spec 139 final suite 1470 passed, 7 retired-UI skips; 122 frontend contracts.

Create real-service fixtures with two companies, dual-role parties, inactive records, mixed units, UTC-boundary commitments/shipments and a corrected shipment. Prove metric totals beyond one contributor page, empty coverage, corrected replacement and source preservation. Test each basic reference create/update, stale revision, foreign ID, unchanged advanced values, idempotent preparation/confirmation and unknown outcomes.

Run focused new Python tests, then full PostgreSQL suite with `PYTHONPATH=src`; run `make lint spec-check`, `make web-build`, frontend contracts/browser and docs build. Browser journeys cover Home/Analytics/chart contributor/case/reference navigation and the four-family create/review/result journey, both widths/themes and all languages.

Use the existing local preview at port 5177 and its separate API/database; do not seed user company data. Record actual results here after execution. Deployment/retirement remain outside scope.

Pre-implementation read-only analysis: 10 requirements, 13 tasks, 100% requirement coverage; no unmapped requirement, constitutional conflict or critical finding. Owner continuation supplies scope authorization; no hooks are configured.

## Implementation and review evidence

- Test-first proof: the initial two service-test families failed collection for the
  missing service modules (`/private/tmp/reality-140-red.log`).
- Final focused service/API gate: 16 passed, including two-connection stale update
  serialization, role-based registers, four-family preservation, same-request and
  same-proposal replay, UTC correction handling, contributor labels and practice
  exclusion (`/private/tmp/reality-140-services-final.log`).
- Frontend contract gate: 123 passed. Localization audit: all four languages have
  1349/1349 recognized UI strings, zero missing or invalid strings. Manually checked
  dynamic customer/supplier labels as well.
- Workspace browser gate: four-family prepare/reload/confirm, lost response with
  read-only outcome recovery, edit revision, unavailable read/retry, empty search,
  keyboard focus and 64 screenshots (Analytics, master data, form, review × four
  languages × two themes × two widths). Reviewed wide Analytics/master data and
  narrow dark review screenshots. Fixed search-field overlap and selected-filter
  appearance found during visual review.
- Existing foundation browser gate passed its full matrix and action/recovery
  journeys; no matrix skip flag was set.
- Authenticated live local preview passed Home → Analytics → delivery → customer,
  and customer prepare without business effect → reload → explicit confirmation →
  receipt → actual persisted reference. This used only `reality_unified_preview_107`
  and created one sample customer (`Keller · Local preview`).
- Source/provenance, roles, item units/tracking, location hierarchy and commercial
  settings are retained by canonical basic updates. No schema or migration changed.
- Ordinary-company reads/preparation and confirmation reject practice tenants;
  existing practice confirmation behavior remains in its existing policy path.
- Original pending preview becomes a receipt after execution in the canonical
  proposal model. The original input remains durable; the UI does not reconstruct
  a past review from today's data.

Final whole-suite status is recorded below only after completion. One earlier
whole-suite run was deliberately interrupted after 1281 passed/6 skipped to include
the final contributor-label and workspace-policy changes; it is not a completed gate.

### Technical review notes

- Contributors are limited before resolving tenant-scoped business labels. Names
  supplement opaque record identities; they never replace identity or joins.
- Register and contributor navigation use the server's clamped page number, so an
  out-of-range bookmark cannot trap Previous on the last page.
- Shared batch updates acquire the same tenant lock as single-record writers.
  Canonical proposal execution claims the proposal first, then locks/reloads and
  checks reference revisions before calling any handler. A pre-handler refusal
  safely restores proposed; unknown handler outcomes remain executing.
- Replay links use each receipt's corresponding input record and PartyRole; a
  company-only Party created by an advanced Chat proposal uses the supporting
  party workspace rather than an invalid customer/supplier link.
- The new shell is still opt-in. Disabling its frontend flag returns presentation
  to the legacy UI while retaining proposal histories and service-level safeguards.
- Owner visual acceptance and broader product retirement are not implied by this
  technical review. No deployment, merge, deletion or schema migration was performed.

## Final verification — 2026-09-07

| Gate | Result | Local evidence |
| --- | --- | --- |
| Full PostgreSQL suite | 1486 passed, 7 existing retired-UI skips, 258.75 s | `/private/tmp/reality-140-full-final.log` |
| Ruff and Spec policy | Passed | `/private/tmp/reality-140-policy-final.log` |
| Web formatting, contracts, localization, build | Passed; 123 contracts; four complete language catalogs | `/private/tmp/reality-140-format-check.log`, `reality-140-contracts-final.log`, `reality-140-i18n-final.log`, `reality-140-web-final.log` |
| Workspace browser | Passed; 64 layout/form/review captures, recovery and server-page correction | `/private/tmp/reality-140-browser-final.log` |
| Foundation browser | Passed; full existing matrix and six action-entry paths | `/private/tmp/reality-140-foundation-browser.log` |
| Authenticated preview journey | Passed against actual isolated API/database | `/private/tmp/reality-140-live.log` |
| Documentation formatting, tests, build | Passed; 45 tests | `/private/tmp/reality-140-docs.log` |
| Diff whitespace check | Passed | `/private/tmp/reality-140-diff-check.log` |

The existing frontend large-chunk advisory remains non-blocking. This increment
adds no dependency or schema. All 13 implementation tasks are complete; owner
visual acceptance, deployment and retirement of supporting workspaces remain
outside this increment's completion claim.

Preview: `http://127.0.0.1:5177/app`, with API port 8007 and the existing isolated
sample company. Screenshot evidence is in `/private/tmp/reality-140-browser/`;
`live-*.png` captures the real local preview, while language/theme fixtures are
explicit test data.
