# Design Review: Company Setup and Demo Data

Date: 2026-09-09. Status: approved, implemented and locally verified; final evidence is in quickstart.md. Earlier design review sections below retain the pre-approval decision history.

## Authorization already present

The owner requested the company setup/demo source feature, approved continuing after spec 147 and explicitly said to proceed. Product intent and preparation of this design are authorized; repeating product-scope approval is unnecessary. No live deployment, destruction of existing data or automatic execution of the Atlas reservation is authorized.

## Original concrete approval gate

The repository Constitution says: “Self-review does not replace human approval for product-scope decisions, schema expansion, exceptions to this Constitution, or merge authorization.” The workflow additionally names architecture/domain review and shortest-link schema proof. The newly concrete proposal is:

1. `ordinary_company_creation`: six-field durable owner/request-to-tenant receipt; Tenant/membership/receipt commit atomically. Sandbox setup continues using PlaygroundRun.
2. `demo_data_connection`: one tenant-owned connection with source/current-schedule links, intended lifecycle, revision/replay and audit timestamps. Reuse ScheduledJob/Run for ongoing run/delivery identity; do not add a DemoRun or queue table.
3. Supporting `(tenant_id, id)` uniqueness on SourceSystem for composite tenant FK integrity.
4. Profile-specific initialization and incoming-order authorization, including existing verified private pending-owner access through owned Playground routes only; no production admission or generic mutation expansion.
5. Queued-only spec 147 cancellation to implement demo pause/stop/future-only resume, preserving normal scheduler pause semantics and all history.

All fields, transitions, lock order, failure semantics and exact test paths are described in data-model.md, plan.md and contracts/. Explicit acceptance of this concrete plan satisfies T001; it must not be recorded as a human schema approval merely because the implementer wrote the plan. Custom requirements-checklist markers remain reviewer-owned.

## Research and decisions

Two read-only research tasks inspected creation/admission/frontend and fixture/service reuse. Local review inspected source intake, interpretation, scheduler and persistence. No runtime file was edited by this feature's planning work; previous spec 147/unrelated workspace changes are retained.

Key findings resolved in the design:

- Ordinary creation commits Tenant before membership and lacks replay identity: use small atomic receipt; do not disguise ordinary companies as PlaygroundRun.
- Pending owners cannot enter ordinary App bootstrap: retain exact owned Playground cockpit and narrowly scoped adapters instead of broad bypass.
- Existing compact/normal-month demos cannot meet canonical counts/dates/provenance: add separate profile, retain lesson helpers and update the company-creation API mapping.
- Existing seed scope is master-data-only and intake commits internally: introduce narrowly reviewed scopes and transaction-bound shared cores, including failure paths.
- Spec 147 pause retains pending retries while demo resume requires future-only arrivals: explicit queued cancellation extension, not hidden special behavior in worker.
- Source progress differs from scheduler success: retained ImportJob/outcome-based counts and visible cap 20; generated demand never executes operational actions.

## Cross-artifact analysis

| ID | Category / severity | Finding | Resolution |
|---|---|---|---|
| A1 | Consistency / high | Pending ready destination could accidentally imply production access | Exact Playground destination and owned routes recorded in company-setup and demo-data contracts |
| A2 | Consistency / high | Generic pause versus future-only demo resume | Narrow queued-only cancellation, T025/026; old generic semantics retained |
| A3 | Transactions / high | Existing committing imports cannot run inside spec 147 handler | Bound cores plus rollback regressions, T004/005/028/029 |
| A4 | Coverage / medium | Legacy company API could retain ordinary seeded creation and bypass shared replay | Delegation/request-key/canonical-Sandbox mapping in contract, T011 and spec 027 reconciliation T035 |
| A5 | Governance / blocking gate | Newly specified schema has no concrete owner acceptance yet | Resolved by explicit owner approval on 2026-09-09; see approval record below |

Metrics: 24 FR/DR, 40 unique tasks, 100% requirement-to-task mapping, nine success criteria mapped, no unmapped task or unresolved product clarification. No unresolved critical design inconsistency. Constitution rows PASS describe conformity; they do not clear the separate pending schema approval. Implementation is intentionally gated.

## Validation of this design package

- Spec Kit feature resolution selects146; existing checkout retained, no feature branch or live deployment created.
- `make spec-check`: PASS.
- Task IDs unique, every FR/DR has test and implementation rows, local links resolve.
- Required runtime/frontend/browser/migration/container checks are specified, not executed or claimed green for spec 146.
- Requirements checklist is the existing spec-quality artifact; the new reliability checklist has 13 unchecked reviewer-owned criteria, assessed technically here and awaiting owner review with the concrete plan.

## Concrete approval — 2026-09-09

The owner explicitly replied “ja freigabe” to the request for approval of this technical plan, both new tables and the bounded Sandbox authorities. This approves the complete proposal above, including supporting uniqueness and queued cancellation. T001 is satisfied. The existing requirements checklist and custom checklist markers are preserved; the explicit review approval supersedes a repeated implementation-gate question. All eight Constitution rows remain PASS; no deployment is authorized. Implementation is now in progress.


## Final cross-artifact review

Spec Kit analysis covers 24 FR/DR requirements, 40 unique tasks and nine success criteria. Every requirement has test and implementation coverage; there are no unmapped tasks, unresolved product clarifications or critical/high design findings. All eight Constitution checks remain PASS. The only final consistency finding was stale planning-status wording in the schema/verification artifacts; implementation bookkeeping updates it without changing the approved scope.

| Requirements | Task coverage | Evidence |
|---|---|---|
| FR-001–007, FR-013 | T008–014, T037 | Shared first/later form, replay/concurrency, admission APIs and 16-case browser matrix |
| FR-008–012, DR-001–004 | T015–023 | Canonical stock/history stories and real separately confirmed reservation receipt |
| FR-014–020 | T024–034 | Connection/rate lifecycle, immutable intake, failure/backpressure, scope and cancellation tests |
| Cross-cutting persistence and policy | T002–007, T036 | Migration/constraint tests, registered tenant boundaries, transaction guards |
| Documentation and release verification | T035–040 | Full backend suite, web/site/docs/lint/spec gates and local Docker acceptance |

Implementation refinements within the approved scope: initialize request intent before the first receipt commit; permit explicit retry of interrupted initialization while keeping reads inert; include the company party in the empty-source prerequisite preview; permit nested savepoint release while rejecting handler root commits; freeze generated business time at durable delivery creation; expose a scoped original-intake read; distinguish HTTP conflict/network errors in source controls. These preserve existing authority, provenance and idempotency contracts.

No CRM/marketing stack, cost/profit authority or automatic operational execution was added. Costs/promotions remain explicitly unavailable. Browser acceptance uses HTTP fixtures; backend and Docker tests separately prove real PostgreSQL behavior. This is local acceptance, not proof of a live Railway rollout. Reviewer-owned checklist markers are unchanged.

Final acceptance: 1538 passed, 9 skipped in 305.29s (0:05:05); 120 frontend contracts; 16 company/source browser combinations plus existing Playground browser journey; 9 container tests; lint/spec/web/site/docs gates PASS. All 40 tasks are complete locally. No release or merge authorization is inferred.

## Live-creation pre-implementation review

The owner's clarification approves FR-021. Plan and T041–044 cover each new behavior, including recovery and completed-request replay. No unresolved clarification, schema change or Constitution conflict. Analysis: FR-021 maps to T041–044; the former manual-only startup language is superseded only for explicitly selected live company creation. Independent manual connection still stops by default. Existing checklist approval remains valid; no repeated gate is required.

Live-creation final review: FR-021 / T041–044 implemented and verified. Full PostgreSQL suite: 1545 passed, 9 skipped in 306.06s (0:05:06); focused service/API 17 passed; browser matrix 16 passed. Shared services, immutable intent and atomic completion preserve Constitution checks. Requirement coverage is now 25 FR/DR with 44 tasks; no unresolved critical/high finding. No schema change or live deployment.

## Authorized local stack integration — 2026-09-09

The owner authorized combining this feature with the actual port-8080 checkout (acab690). Preserve the unified app and retired legacy browser routes. Port shared services and source controls into unified CompanySettings/DataSourcesPage; do not restore the old App. Active destinations use /app. Existing pending-admission presentation remains unchanged. Join migration branches with a no-DDL merge revision after the already-tested additive queue/setup migrations, retaining lot expiry. Back up the local database, rehearse upgrade on a restored disposable database, build matching services, and verify the actual localhost surface before replacing the running local containers. No remote deployment or Git merge/commit is implied. Constitution remains PASS; preservation of current domain changes and scoped service authorities are mandatory.

## Final unified-app / company-card review

FR-022 maps to T050; T045–049 cover the authorized combined local rollout. No schema
or permission expansion was needed for list metadata. Existing ordinary bootstrap
shape is preserved; practice profile/source metadata is read through the scoped
service. Buttons remain inside their company card and target that company ID.
The current unified app, inspectors, lot expiry and retired legacy routes are retained.

Verification: 1913 backend tests passed, nine conditional skips; 40 frontend contracts;
16/16 browser combinations against the actual port-8080 build. Lint, spec policy, web,
site and docs gates pass. Backup rehearsal and actual migration preserved all old rows
in 62 tables / 38 tenants. Matching application processes and independent scheduler /
worker run successfully. No unresolved critical/high finding. Local deployment only;
reviewer-owned approval markers remain unchanged. See quickstart.md for exact evidence.

FR-023 pre-implementation review: the user explicitly approved the three goal-based choices and demo-only live toggle. Maps to T051–053; no unresolved clarification or critical finding. Eligibility, business semantics and API contracts remain unchanged. Existing checklist approval persists (requirements 23 checked; reviewer-owned 13 unchecked markers remain untouched). Verification scope is frontend/browser plus spec/docs; backend and migration suites need no rerun for this presentation-only change.

FR-023 completed: the updated browser assertion first failed against the old form (0 vs 3 goal-choice radios). The new preview build passes 16 language/theme/viewport combinations, including default choice, one fieldset, demo-only toggle, clearing live intent on selection change, live request mapping and recovery. Desktop screenshot reviewed. Forty frontend contracts, formatting, i18n audit, TypeScript/Vite, spec policy and docs build pass. Only the local web image/container was updated; backend, database and scheduler remain unchanged. No backend/migration rerun was required for this presentation-only refinement.

FR-024 review: user requested actionable missing-name feedback. T054 covers name validation and correction without authority/API changes. Existing approval applies; no unresolved clarification or critical finding. Frontend/browser verification is proportional; no backend/schema change.

FR-024 / T054 complete: red proof demonstrated the disabled button prevented feedback. Forty frontend contracts, formatting, four-language audit, TypeScript/Vite, spec policy and docs build passed. Sixteen browser combinations passed empty/whitespace rejection with no setup request, inline invalid state, focused field, correction, retained demo/live choices and successful creation/recovery. Only the local web container was updated; backend and database unchanged.

FR-025 pre-implementation review: user requests removing the unexplained post-creation decision. T055 maps automatic entry, destination feedback and failure recovery. No unresolved clarification or critical finding; shared services and startup consent unchanged. Frontend/browser checks are sufficient for this adapter-only change.

FR-025/T055 complete: prior ready menu failed the new auto-open regression. The updated build passed 16 browser combinations covering direct automatic entry, failed-opening receipt recovery after reload, one creation request and destination confirmation. Forty frontend contracts, formatting/i18n, TypeScript/Vite, spec policy and docs build pass. Local web image/container updated; backend, source state and database unchanged.

## Sandbox clarity and live activity refinement

User explicitly approved both UX changes and live widget; Reports is an existing unified Sandbox read regression. FR-026–028 map to T056–058. No unresolved clarification/critical finding. Existing review approval applies; no ordinary Sandbox writes authorized. Tests cover scoped reads, chronological ordering, default cursor, polling, state preservation and UI clarity.

FR-029 approved by latest user steering. T059 covers route and navigation; existing API/backend fixes remain in scope and full backend verification continues. No new permission or clarification needed.

## FR-026–029 final acceptance — 2026-09-09

UX review produced compact state/control groups, persisted-time activity and a header badge. User steering moved Demo Data to its own Company navigation destination. Initial regressions reproduced the Sandbox report denial and missing recent-read mode; an older test enforcing the superseded analytics denial was updated while preserving reference-workspace restrictions. Direct-entry regression additionally caught the outer route allowlist and is now green.

- Full backend: **1914 passed, 9 skipped in 343.80s**; focused read/API/security checks: 76 passed.
- Web: 41 contracts, formatting, four-language audit, TypeScript/Vite, lint, spec policy and docs build PASS.
- Dedicated page: 16 browser combinations PASS: four English functional cases and twelve localized visual cases; menu placement/visibility, standalone route, no widget in Integrations, polling, stale retention, input/confirmation preservation and confirmed controls checked. Spanish mobile badge overflow fixed and verified; badge has accessible description.
- Existing creation/recovery browser matrix: 16 PASS before navigation refinement; direct dedicated-page routing/navigation is covered by the final matrix and entry contract.
- Existing Demo Firma 1 Live verified through the deployed API image with SET TRANSACTION READ ONLY: Reports/contributors both 34 open, latest snapshot 25 of 26 imports in chronological order, running source, zero pending/failed. Simulation continued during work.
- Matching local API/MCP/background images and web updated. API/MCP healthy; scheduler/worker running without restarts. Port 8080 serves the tested dedicated-page build and API exposes recent mode. No schema migration, source restart command or business mutation was performed by verification.

T056–059 complete. No unresolved critical/high review finding. Reviewer-owned checklist markers unchanged; no remote deployment.

## FR-030 review
The reported Demo Sandbox Exceptions failure is reproduced by both the seeded demo
service path and the authorized practice HTTP path (HTTP400). Only the register and
detail read guards change to scoped tenant existence. No schema, frontend, canonical
exception logic or mutation authorization changes. Existing foreign finding and
practice mutation tests remain green in the focused suite (81 tests).
