# Research: Company Setup and Continuous Demo Data

Date: 2026-09-09. Repository inspection, including two read-only research agents requested by the Spec Kit planning workflow. No runtime implementation or deployment in this planning phase.

## Shared creation surface

- Decision: extract a shared `CompanySetupForm.tsx` used by first onboarding and all three later company-create entry points in `App.tsx`; expose account-scoped setup services/API. Reuse `user.application.company_name` only for the first editable default.
- Evidence: `CompanyOnboarding` currently combines ordinary creation with compact guided demo; later `SimpleCreateModal` forms submit name only. `web/api.py:create_company` calls committing `create_tenant`, commits membership separately and then optionally seeds.
- Rationale: one reviewed request and explicit ready destination eliminates duplicate company entry and orphaned creation.
- Rejected: renaming existing companies from application data, hiding a second Playground creation screen, or changing the old compact lesson globally.

## Admission and Sandbox routing

- Decision: preserve immutable `Tenant.purpose`, existing verified-owner practice policy, feature flag and quotas. Active users enter the existing App practice/company workspace; pending users enter the exact created Playground cockpit. Existing membership/invitation routing remains first.
- Evidence: `tenant_policy.py:practice_company_runs` explicitly requires active status; pending accounts are currently restricted to `/api/playground`. No broad pending exemption for bootstrap or `/api/companies` is permitted.
- Decision: pending users' setup and demo controls use narrowly allowlisted account/owned-Playground endpoints calling the same application services as active users. This grants no production route, arbitrary tenant override or general mutation capability.
- Narrow profile initialization and incoming-order scopes must be separately reviewed; existing `_SEED_OPERATIONS` permits master data only.

## Persistence reuse

- Decision: Sandbox initialization reuses `PlaygroundRun` owner/request uniqueness, lifecycle, bounded manifest and persisted failure identity. Add separate presets; retain every existing lesson preset.
- Decision: propose one small ordinary-company creation receipt and one Demo Data connection table; see data-model.md. Cross-content/environment retries serialize on the owner and check both receipt and Playground request namespaces.
- Decision: a new spec 147 ScheduledJob represents each continuous Start-after-Stop run. Its opaque identity, immutable delivery snapshots and retained history already provide run identity; do not add a DemoRun or delivery queue table. SourceRecord, ImportJob and interpretation outcomes remain the source-progress authorities.
- Rejected: an ordinary company disguised as a PlaygroundRun; mutable connector JSON hidden in SourceSystem.description; fake SourceRecords or ChangeProposals used as setup receipts; another scheduler/worker.

## Canonical profile

- Decision: add an independent `international-v1` profile: 16 items, four customers, three suppliers, one company party, two locations; 84 days split into adjacent 42-day windows ending at anchor UTC midnight.
- Evidence: normal_month has five items, a fixed local period, internal commits and a backdated proposal timestamp. Existing Playground lesson has three items and no opening stock. Neither is the canonical fixture.
- Decision: share one pure catalog and explicit source-stated fixture payloads among both company entry points and the minimal integration prerequisites. Keep categories as source/manifest content and unsupported costs/promotions absent.
- Execution repeats create fresh isolated execution-profile practice tenants; no destructive reset or synthetic confirmed proposal. The execution-profile marker blocks Demo Data connection.

## Source intake and transaction ownership

- Decision: register a genuine `demo_data.order` interpreter in the existing source registry. Reuse shared evidence/commitment helpers; do not pretend synthetic orders are Shopify or regenerate their payload through `create_manual_order`, which hardcodes manual identity.
- Evidence: `enqueue_source`, `process_import_job`, reserve/hold and parts of seed orchestration commit internally. Existing `_commit=False` service patterns establish a caller-owned transaction convention.
- Decision: extract transaction-bound intake/interpretation cores and seed-required helper variants. Existing public callers retain their present commit/error behavior. Scheduler handlers use only the bound cores, with savepoint rollback for interpretation failure and retained intake/outcome evidence. Never suppress Session.commit through a custom session subclass.
- Generate one source order and attempt its normal interpretation per scheduled occurrence. A recorded failed ImportJob remains failed/pending in source status; a successful scheduler handoff does not claim successful import. At 20 pending/failed generated imports, generation pauses visibly; retry uses the same ImportJob/source identity and requires explicit control after permanent failure.

## Timing and controls

- Decision: use `demo.generate_orders`, rates 10/60/300 per hour (intervals 360/60/12 seconds), default 60, stopped initial connection. All Start/resume/rate changes begin after a fresh interval.
- Spec 147 preserves paused pending occurrences. Therefore add a narrow queued-occurrence cancellation service: pending/retry only, never an executing claim, retained cancelled history. Demo pause/stop uses this service after pausing the schedule so resume cannot replay stale arrivals. This is a small spec 147 contract extension, not a separate queue policy.
- Lock order: discover the current pointer without mutation, then schedule → current unfinished run → connection; revalidate pointer/revision after locking. Control and generation share that order. A run already executing may finish before control acknowledgement.
- Stable external identity includes continuous schedule ID and logical scheduled-run ID. Deterministic choices derive from the recorded seed and logical occurrence identity, while actual business timestamps remain distinct. Retry reuses stored payload; no new timestamp/version on replay.

## Required review

The user authorized continuation of the product work. The concrete two-table schema, source-system composite uniqueness, profile-specific authority and narrow queued cancellation are newly specified here. Repository constitution/workflow requires explicit schema approval after this reviewable design; no migration or runtime behavior is changed before that gate.
