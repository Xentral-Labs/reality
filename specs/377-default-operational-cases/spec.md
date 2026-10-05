# Default operational cases for every company

**Feature**: `377-default-operational-cases`
**Created**: 2026-10-05
**Language**: English
**Status**: Implemented on `feat/default-operational-cases`; targeted checks pass. Full regression and final PR review are in progress. Simulator runtime integration, external-runner and multi-day gates remain pending.
**Input**: Make the operational-case logic introduced by PR #378 the product default for all companies, without an owner activation switch. Prepare this specification for another code agent; do not implement the rollout in this handoff.

## Context and Intent

### Problem

Spec 371 currently requires owner-confirmed adoption. A company can therefore run orders without coordination until someone activates the feature. The live company simulator also requires a manual setup step. The new product version should supply the same responsibility and stale-work protection consistently, without a per-company activation action.

### Scope

- Default operational-case coordination for every new and existing company, including simulator/test companies.
- Automatic inclusion of accepted outstanding sales-order customer-delivery work and accepted open return announcements supported by spec 371.
- An upgrade/backfill path, safe concurrent new intake, shared-job reconciliation and removal of activation UI.
- Preservation of existing case identity, manual ownership, revisions, bindings, takeover/handback history and uncertain execution.
- Updated operator instructions, public contracts and regression coverage.

### Non-Goals

- Adding supplier, Finance, warehouse, refund or other case families absent from spec 371.
- Automatically approving, purchasing, dispatching, refunding, sending mail or starting an external model.
- Granting an agent human identity, approval rights or unrestricted business authority.
- Creating active cases for completed historical work, importing unaccepted raw Sources as goals, or rebuilding business balances.
- A workflow designer, separate scheduler/queue, persisted fulfillment status or silent rollback of existing manual takeovers.

## User Scenarios & Testing

### 1. New company works without activation (P1)

Given an ordinary newly created company, when its first supported order is accepted through a canonical path, exactly one fulfillment case exists and automation guards apply. No activation request, UI switch, simulator-specific enable command or fabricated owner approval is needed. An incoming email alone creates no operational goal.

### 2. Existing company upgrades safely (P1)

Given an unadopted company with open, partially fulfilled, cancelled and completed orders plus open/closed return announcements, upgrading includes only currently outstanding supported goals. Two lines of one order share one case; an open return remains a separate goal. Stock, commitments, movements, money and original Sources are unchanged. Repeated rollout and restart do not duplicate cases or bindings.

### 3. Existing intervention remains authoritative (P1)

Given an adopted company with a manually owned case, revision-bound proposals and an unsettled execution, upgrading preserves all of them. Automation still refuses manual ownership, stale reviews and uncertain outcomes. Handback uses the existing exact reviewed confirmation; previously obsolete approvals never become valid again.

### 4. Simulator exercises ordinary behavior (P2)

Given a default live simulator company, accepted orders acquire cases without owner setup. The external operator discovers cases, respects manual takeover and continues unrelated eligible work. The simulator does not adopt a second implementation of coordination or introduce supplier/Finance cases.

## Requirements

### Functional Requirements

- **FR-001**: **Default coverage**. After the version upgrade, supported coordination applies to all companies without a per-company opt-in. New-company creation and canonical accepted-work paths must not leave an unguarded activation gap. Preserve archive/membership restrictions; a company with no active owner must not require an invented owner to establish internal coordination.
- **FR-002**: **Canonical goals**. Reuse spec 371's anchors and policies. One sales order has one fulfillment case for its customer-delivery commitments; each supported accepted open ReturnAnnouncement has its own return case. Staged intake, raw mail, invoice/payment evidence and unrelated business objects never become goals merely because coordination is default.
- **FR-003**: **Existing outstanding work**. Upgrade/backfill covers all existing companies, not only rows already present in CaseAdoption. Determine eligibility from canonical current facts, including partial fulfillment, cancellation, applicable corrections and open return status. Fully closed history is excluded. A later supported correction/reopening must receive guarded coverage and reuse an existing anchored identity when present.
- **FR-004**: **Preserve controls**. Retain case IDs, human ownership, takeover users, control revisions, case/proposal links, exact review history and real execution outcomes. Default activation must not reset a case to automation, approve old work or assert external cancellation.
- **FR-005**: **Guards before effects**. Across API, CLI, MCP, Chat, workers and canonical services, case responsibility/current-state/source-coverage checks remain authoritative before automated business effects. Caller-supplied IDs, omitted IDs, alternative channels and consumer delay cannot bypass them. Default coverage must not itself authorize any business action.
- **FR-006**: **Safe rollout**. Backfill is tenant-scoped, bounded, durable, restartable and idempotent. New intake concurrent with backfill cannot escape guards or create duplicate cases. Define upgrade readiness so a process cannot report full coverage while existing supported work is unprotected. Scheduler/worker startup must not perform schema migrations. Missing migration/backfill readiness must be explicit rather than silently disabling guards.
- **FR-007**: **Honest job authority**. Reuse the shared registry/queue and bounded reconciliation. Version-driven coordination must have truthful platform/internal attribution, not fabricated user consent, an arbitrarily selected owner, or an external token impersonating a human. Preserve meaningful historical owner-approved attribution. Internal database coordination must not grant provider transport or business-effect permissions.
- **FR-008**: **UI and compatibility**. Remove the owner activation button/dialog and disabled/adoption instructions from the normal UI. Keep case discovery, takeover, exact handback, Source links and failure containment. Define compatibility for existing adoption/status endpoints and clients; retries must not reset responsibility. Report upgrade failure/incomplete coverage explicitly, without an end-user enable toggle.
- **FR-009**: **Simulator and documentation**. Update the live simulator guide/startprompt, README, its opt-in regression, spec 376 FR-019, durable operational-case contract and affected Web/public guides. The operator should verify available coordination and readiness, not activate it. Still inspect case ownership and prepare fresh work after handback. Pending external-runner and multi-day capacity gates remain pending.
- **FR-010**: **Business invariants**. The rollout must produce no orders, fulfillment, reservations, movements, financial postings, allocation changes, outgoing mail or provider calls. Never store business balances/status on a case. Case identity and event checkpoints are coordination, not business truth.
- **FR-011**: **Evidence and compatibility**. Preserve existing immutable Sources and executed receipts. Record version-driven rollout provenance honestly and distinguish it from old owner adoption. Identify the minimum necessary schema changes in the plan; retain tenant/composite foreign keys and exact action bindings. No destructive downgrade that discards responsibility history may be advertised as safe.

## Requirement Traceability

| Proof | Requirements |
|---|---|
| New ordinary company, accepted order with two lines, no adoption call; one case immediately | FR-001,002,005 |
| New live simulator company, intake replay and consumer replay; one stable case | FR-001,002,009 |
| Existing unadopted company: open/partial orders and open returns included; cancelled/fulfilled orders and closed returns excluded | FR-003,010 |
| Previously adopted company: exact IDs, manual takeover, revisions, bindings and unsettled execution retained | FR-004,011 |
| Rollout interruption/retry, concurrent intake, supported correction/reopening and delayed consumer | FR-003,005,006 |
| Cross-tenant references refused; raw Sources/intake preparation cannot create accepted goals | FR-002,005,006 |
| Automated work refused after takeover and on obsolete review; newly reviewed work allowed after exact handback | FR-004,005 |
| Company without an active owner: truthful coordination scheduling; no fabricated approval or business authority | FR-001,007 |
| Shared job execution/recovery, migration readiness and bounded large-history backfill | FR-006,007,011 |
| Real browser: no enable control, cases discoverable, takeover/handback still confirmed, stale/malformed responses contained | FR-008 |
| Before/after exact business records and immutable payloads: no business effects/provider calls from rollout | FR-010,011 |
| Legacy adoption/status client behavior and generated documentation consistency | FR-008,009,011 |

## Success Criteria

- **SC-001**: Every new supported accepted goal is protected without a company activation request.
- **SC-002**: Restartable backfill proves complete supported outstanding coverage for every existing company, with no duplicate cases or changed business records.
- **SC-003**: Existing manual ownership and stale-action fencing survive the upgrade, with passing exact takeover/handback and tenant-isolation proofs.
- **SC-004**: Activation controls are absent, required local/CI gates pass, and operator instructions match the implemented rollout.

Success means every supported outstanding goal has guarded coordination after upgrade, new work is covered without setup, historical control state is preserved, activation UI is absent, and required local/CI gates pass. Specify exact backfill completion evidence; configured rollout is not proof of completion.

## Assumptions and Dependencies

- PR #378/spec 371 supplies the existing case layer, policies, migration 0144 and guards. Check current main before planning; feature/migration numbering may have moved.
- User requested default-on product behavior for all companies and removal of manual activation. This is not authorization for unrelated business effects, production deployment or destructive downgrade.
- Spec 376 supplies the live company simulator; integrate its changes if available rather than rebuilding it.
- PostgreSQL is the supported database; UTC, Decimal, immutable Sources, tenant scope and shared services remain mandatory.
- Technical attribution, readiness/backfill strategy, schema changes and compatibility design must be resolved in the implementation plan and Constitution review before coding. This document does not claim those decisions or any runtime rollout are completed.
