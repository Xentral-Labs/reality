# Historical implementation handoff

The default-on implementation is now on main; the current spec, plan and runtime take precedence over this original design handoff.

# Implementation handoff

## Copyable code-agent task

```text
Implement specs/377-default-operational-cases/spec.md in this repository.
Read AGENTS.md, .specify/memory/constitution.md and docs/SPEC_DRIVEN_WORKFLOW.md.
The requested product behavior is default operational-case coordination for all
companies without an activation switch, including existing outstanding work and
new simulator companies. Preserve manual takeover, exact handback, stale-action
fencing, current source coverage and existing permissions.

Start from current main in an isolated feature branch/worktree. Locate PR #378's
actual merged code and spec 371; obtain this specification from the simulator
branch if it is not yet on main. Recheck feature numbering before committing.
Do not implement an activation workaround only in the simulator or merely hide
its switch. Do not fabricate an owner decision to satisfy current job constraints.

Create/review plan.md, any justified data-model/migration contract, tasks.md and
requirement-to-test mapping. Follow the repository specify/review/plan/analyze
workflow and resolve critical findings before coding. The product direction has
already been requested; architecture/schema exceptions still need the repository's
applicable review. Choose the smallest truthful attribution and rollout design.

Write meaningful failing tests first where practical. Implement through canonical
services and the existing shared scheduler/worker; adapters must not write ORM.
Cover ordinary company setup, all supported acceptance paths, existing unadopted
companies, partial work, open returns, concurrent intake/backfill, retries, retained
human ownership, old proposals, unknown execution, tenant isolation, no-owner
companies and unchanged business records. Keep unsupported case families explicit.

Remove activation UI and update compatibility behavior, documentation, simulator
startprompt and the opt-in assumptions of its tests/spec 376 FR-019. Case adoption
must not approve purchases, dispatches, refunds, mail or launch an external model.

Run required backend, migration, Web/browser/localization, generated-documentation
and CI gates appropriate to the change. Do not mark acceptance complete with red
checks or an untested rollout. Prepare a separate PR describing before/after behavior,
backfill/readiness/provenance, rollback limitations and exact test evidence.
Do not merge or deploy to production as part of this task.
```

## Concrete integration hazards to resolve

These are findings from the current simulator checkout, not an approved schema design:

- `services/operational_cases.py`: `adoption()` currently gates case creation, reads,
  guards and consumer work. Eligibility uses an adoption capture boundary and selected
  historical IDs; changing only an enabled boolean misses existing work.
- `db/operational_cases.py`: CaseAdoption currently requires a decision FK. Existing
  owner adoption/history must remain distinguishable from version-driven default policy.
- `services/case_jobs.py`: tenant discovery starts from CaseAdoption; enqueue derives
  the actor from the adopting decision's `decided_by_user_id`.
- `jobs/handlers/operational_cases.py`: reconciliation currently requires a company
  owner. Do not select an arbitrary member or attribute system rollout to that user.
- `db/scheduled_jobs.py`: `ck_scheduled_run_actor` currently allows actor-less runs
  only for `projections.refresh`. A truthful internal case job requires a reviewed
  shared-queue/authorization design, not pretending to be a projection job or broadly
  disabling authorization on other job types.
- `services/case_action_guards.py`: existing unanchored-operation restrictions and
  business review/current control checks must still apply consistently. Assess legacy
  pending work compatibility explicitly; never bypass takeover to retain an old test.
- `web/operational_cases.py` and `apps/web/src/unified/OperationalCaseDetail.tsx`:
  adoption/status APIs and enable UI require coordinated compatibility changes.
- `scenarios/company_simulator/LIVE.md` and
  `tests/scenarios/test_live_company.py`: currently describe/assert explicit adoption;
  rewrite for ordinary default behavior and keep actual takeover/handback proof.

Also inspect case policies, migrations, tenant-isolation/catalog declarations,
company setup, scheduler/worker deployment contracts, browser fixtures and public
operator guides. Update existing opt-in tests intentionally; do not delete the
responsibility, exact-review or cross-tenant safety assertions to make them pass.

## Handoff status

Only product specification and implementation instructions are prepared. No runtime,
schema, UI, adoption record or business data has been changed by this handoff.
The next agent owns technical planning, implementation and verification.
