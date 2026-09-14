# Feature Specification: Playground Practice Companies

**Feature Branch**: feature/playground-free-operations
**Created**: 2026-09-07
**Status**: Approved
**Language**: English
**Input**: Owner approved quick experiments versus persistent named practice companies.

## Context and Intent

### Problem
Starting a fresh sandbox currently archives the active experiment. A learner needs a
stable practice company to return to while trying other examples independently.

### Scope
Choose Quick experiment or Practice company before confirmation. Name the practice
company and reopen it from saved sandboxes. Keep its records across other starts.

### Non-Goals
Production-company linking, data copying, sharing, automatic deletion, conversion of
existing runs, renaming, new ERP rules, and new deletion/archive controls are excluded.

### Existing Contracts
[Playground](../096-learning-playground/spec.md), [free operations](../103-playground-free-operations/spec.md),
[Web](../../docs/WEB_SPEC.md).

## User Scenarios & Testing

### User Story 1 - Create a named practice company (Priority: P1)
**Why this priority**: A stable private business can accumulate learning activity.
**Independent Test**: Create a named company, reload and reopen with the same references.
**Acceptance Scenarios**:
1. Choose a practice company, enter a nonblank name, review and confirm; its name
   appears in the saved list, cockpit and own-company reference.
2. Retry a lost setup response with the same request; no second company is created.
3. Blank or overlong names and changed retry identities are rejected without writes.

### User Story 2 - Keep companies while experimenting (Priority: P1)
**Why this priority**: Separate exercises must not retire an ongoing learning business.
**Independent Test**: Create company A, quick experiment, company B, another quick
experiment; A and B remain editable with identical records and distinct identities.
**Acceptance Scenarios**:
1. Starting another sandbox never archives a practice company.
2. Replacing a quick experiment retains the current explicit archive confirmation.
3. Saved companies are directly selectable; production and another account stay isolated.

### Edge Cases
Concurrent starts, lost responses, failed initialization, old clients, quotas, archived
history, duplicate display names, whitespace, pending setup, other-owner access.

## Requirements

### Functional Requirements
- **FR-008**: An active permanent practice company is selectable in the normal App
  by its verified, active owner, with a persistent Sandbox label. Both surfaces use
  the same tenant and records. App master data, evidence imports, operational and
  financial actions use normal shared services and confirmation rules; not read-only.
  The App links directly to its Playground run and the Playground links to that
  tenant in the App. Existing practice companies gain access without conversion.
- **FR-009**: Temporary runs retain their existing isolated policy. Foreign users,
  including administrators without ownership, do not discover or operate another
  practice company. Disabled, unverified or revoked owners and inactive practice
  companies cannot write. Production tenants cannot be passed into simulations.
  Live connector installation, external delivery and invitations remain forbidden;
  this increment does not change company lifecycle or sharing. Unknown operation
  names fail closed. Playground-scoped execution cannot use App authority to escape
  its reviewed intent. Local App changes remain visible to fresh Simulator reads and
  invalidate stale proposals through the existing revision checks.
- **FR-001**: Offer quick experiment (default) and named practice company with explicit
  confirmation. Practice names are trimmed, required and at most 120 characters.
- **FR-002**: Keep practice companies active when any other sandbox starts. Multiple
  practice companies may coexist; quick replacement archives only a quick experiment.
- **FR-003**: Persist and show kind and company name in entry and cockpit; reopen the
  same company without reinitializing data. Existing runs remain quick experiments.
- **FR-004**: Creation retries retain kind/name/preset and request identity. Changed
  input with a used key conflicts; unfinished setup remains safely retryable.
- **FR-005**: Creation review has one New sandbox heading and a shared action row
  with a primary Create sandbox and clearly outlined Cancel button. No Refresh
  action is shown during review. Cancellation creates nothing; existing retry
  and confirmation semantics remain unchanged. Both themes and mobile stay usable.
- **FR-006**: Selecting an unavailable customer return explains the missing shipment
  and offers a return to operations without writes. Guided editors always offer an
  exit before preparing the next action. When earlier steps have executed, an exit
  notice explains that leaving does not undo records and asks the learner to consider
  a return, reversal or compensating operation. Unknown execution cannot be cancelled
  through this exit; proposed actions retain explicit rejection.

### Domain and Traceability Requirements
- **FR-007**: Needs attention offers an accessible information control opening the
  current canonical exception-class catalog, including all classes even with no
  active findings. Searchable labels and expandable business descriptions, ownership
  and resolution guidance explain when findings appear. Reload metadata on each
  opening; show loading/error/retry honestly. Catalog membership is not an active
  finding or a claim that every class is reproducible with Playground operations.
  No duplicate class list or business derivation is introduced in the client.

- **DR-001**: Each sandbox owns a distinct private sandbox tenant. Use the same
  confirmed services and retain owner isolation, quotas and production separation.
- **DR-002**: No operational balances/statuses are added. Company naming changes only
  setup references; business records and source/evidence relationships stay unchanged.

### Key Entities
Sandbox has a usage kind and its existing tenant. The tenant owns the company name;
the own-company party is initialized with that name. Display names are not identities.

## Success Criteria
- **SC-001**: After alternating four sandbox starts, both named companies reopen with
  unchanged identities and references and remain writable.
- **SC-002**: All requirements have service/API/browser proof; old runs remain readable.

## Assumptions and Dependencies
Temporary means intended for short experiments, not automatic expiry. No user data is
deleted. Names need not be unique. Existing sandbox account and feature gates apply.
No production tenant is selected or linked. Owner approved this isolated-company model.

## Open Questions
None within this increment.

## Company switcher sizing
- FR-010: The company menu grows into available viewport height instead of limiting
  its company list to four rows. Overflow remains scrollable on short screens and
  with many companies; account actions remain reachable. Company eligibility is unchanged.
- Acceptance: five companies fit without list scrolling on a tall desktop; a long
  list remains contained and scrollable on a short viewport.

## Requirement Traceability
| Requirement | Scenario | Proof |
|---|---|---|
| FR-001, FR-003, DR-002 | US1 | Named setup/reload, UI labels |
| FR-002, DR-001, SC-001 | US2 | Alternating starts, restart refusal, owner tests |
| FR-004, SC-002 | Both | Retry, invalid input, migration and browser tests |
