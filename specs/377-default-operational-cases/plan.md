# Implementation plan: default operational cases

**Branch**: `feat/default-operational-cases` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

## Summary and technical context

Replace the per-company adoption gate with version-owned coordination. Python 3.12,
SQLAlchemy 2, PostgreSQL, Alembic, existing FastAPI/tools and React surfaces remain.
Reuse spec 371 anchors, exact action guards and shared registry/queue. No provider calls.
PR #378 is on main as f3832168. Simulator spec 376 remains on its own branch; import
only the integration instructions/spec and its relevant regression for follow-up integration.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Only accepted commitments/announcements supply anchors; Sources untouched. |
| Operational authority | PASS | Current open quantity/status stays derived from Reality. |
| Proven schema | PASS | One tenant rollout row stores resumable cursors and version provenance, no business status. |
| Tenant/service boundaries | PASS | Tenant lock, scoped scans, existing services and composite links. |
| Specification/test evidence | PASS | Requested scope accepted in handoff; regression tests precede implementation. |
| Explainable web | PASS | Preserve discovery/control/source links; expose incomplete upgrade without activation. |
| Simplicity/storage | PASS | Existing PostgreSQL shared queue; narrow internal authorization copied from projections. |
| Received values | PASS | No balances, amounts or source values changed. |

No constitutional exception or new external-effect infrastructure is required. Technical
review includes independent planning research; final schema/domain approval remains PR review.

## Design and exact paths

`db/operational_cases.py` adds CaseRollout: tenant FK/PK, rollout version 377, two
nullable ID cursors (empty string means scan start, NULL means scan done), completion
and creation times. Version itself records platform provenance; no owner decision FK.
Historical CaseAdoption remains unchanged. Migration 0145 adds this table and narrowly
permits actorless unscheduled `operational_cases.reconcile` runs. Downgrade refuses
any existing case, populated rollout history or internal runs; no destructive downgrade advertised.

`services/operational_cases.py` supplies enabled/status, initializes rollout/checkpoint
under the tenant delivery lock, scans at most 100 canonical supported records per run,
and commits cursors/cases with the existing event consumer. Missing checkpoint starts
at current event progress; existing checkpoints are retained. Completion requires
both scans and event catch-up under the same lock. Scheduler discovers every active
tenant with missing/incomplete rollout or event lag via outer joins in `case_jobs.py`.
New canonical acceptance and supported corrections synchronously ensure case coverage.
Guards ensure the referenced outstanding goal under the same lock before effects,
even during backfill. Old proposals without exact case reviews/bindings fail stale;
executed receipts remain intact. Closed history creates no new cases. Internal
authority authorizes only persisted actorless unscheduled matching runs for active
tenants; legacy owner runs keep their current owner check. Public run/schedule creation
cannot select this internal job. Rollout never grants business permissions.

Legacy adoption remains a confirmed owner-authenticated compatibility acknowledgement:
validate same-company selections but create no adoption/decision and never reset cases.
Status keeps adopted=true/can_adopt=false compatibility fields and reports coverage,
provenance and job failure; incomplete migration is explicit. Reads never run backfill.
`web/operational_cases.py`, `OperationalCaseDetail.tsx` remove activation and display
upgrade readiness. Owned sandbox status reads follow existing private read access
and report can_control=false without granting business-member authority.
Takeover/handback and malformed response containment remain.

## Verification and risks

New `tests/test_default_operational_cases.py`: immediate multi-line default coverage,
no-owner internal queue, bounded rollback/restart, legacy records/backfill, unchanged
business records, manual responsibility/proposal/unknown outcomes, tenant scope,
correction/reopening, migration failure. Update existing opt-in tests intentionally.
Add migration roundtrip/refusal and concurrent separate-session proof. Run full backend,
Ruff, spec policy, generated docs, Web build/localization, browser suite and docs tests.

Simulator dependency remains separate: preserve its pending external-runner/multi-day
gates. Import changed simulator docs and test with explicit integration provenance.
Operational risk: backfill completion requires scheduler/worker operation, exposed as
incomplete until proved; guarded new work does not wait for it. Deploy migration first,
then matching services/scheduler/worker. Startup never performs migrations.

## Shared claim fairness refinement

Live-stack CI exposed that enqueue alternation alone cannot protect source latency:
FIFO claims drain old projection/case work before a newly due source occurrence.
Independent technical review confirms a bounded foreground/background claim alternation
using the last actual `started_at`, not enqueue chronology. Only actorless
`projections.refresh` and `operational_cases.reconcile` belong to the internal class;
legacy actorful cases retain their classification and authorization. Try at most 100
eligible candidates in the preferred class, then at most 100 in the other class if
locks make the first unavailable. Existing definitive failure verdicts still stop a
claim; eligibility, lease identity, retry time/limits and authorization are unchanged.

A partial tenant/started_at/id index on already-retained claim history supports the
latest-claim lookup without scanning every retained run. Add it in unmerged migration
0145 and metadata; it introduces no new authority or status field. Meaningful tests
first prove a >100-run internal backlog cannot hide foreground work, both classes make
progress, and locked preferred candidates permit bounded fallback. Existing lease,
unknown-outcome, actorful owner and complete live source proofs remain required.

The existing immutable `normal-month.v2` fixture retains its deliberately orphaned
return. Independent review accepts a non-automatic execution scope around only that
authored movement, after the existing exact confirmed fixed-setup authority check.
The scope grants no principal, leaves business mutation validation intact, and
restores the surrounding automatic context. Its regression proves that a later
unanchored automatic return still refuses without effects; original month exception
assertions remain unchanged.
