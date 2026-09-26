# Feature Specification: Decision points in the business timeline

**Language**: English

**Created**: 2026-09-26
**Status**: Approved for implementation
**Input**: Add Decisions to the existing business timeline as individual points, without connecting decision lifecycle stages.

## Context and Intent

### Problem
The business timeline shows recorded operational changes but omits the approval decisions that preceded them. Users cannot see when a proposed change entered the queue or when it was accepted or rejected.

### Scope
Add a Decisions lane to the all-activity timeline. Plot proposal creation and settlement as separate points using the existing tenant-scoped decision register read. The points are not connected. Keep selected-order journeys exact: decisions are not plotted there until the domain holds an explicit order relationship.

### Non-Goals
No inferred proposal-to-order relationship, lifecycle line, schema change, new business event, mutation, or change to decision approval. No claim that a proposal caused an operational record merely because their time or payload is similar.

## User Scenarios & Testing

### US1 — See decisions in business time (P1)
Open the all-activity timeline and see when decisions arose and when they were accepted or rejected.

Acceptance:
1. A pending proposal produces one raised point at `created_at`.
2. A settled proposal produces a raised point and a separate accepted or rejected point at `decided_at`.
3. Decision points have no lifecycle connector; overlapping points use the existing counted collision behavior.
4. Selecting a decision point identifies the stage and opens the existing decision history.
5. Selecting a sales order hides the tenant-wide decision points rather than implying order membership.

## Requirements

- **FR-001**: The all-activity timeline MUST show a localized Decisions lane with the caption “What was decided”.
- **FR-002**: Each loaded proposal MUST produce a raised point at creation and, when `decided_at` is held, one accepted or rejected point at settlement. Unknown terminal statuses MUST use neutral settled wording.
- **FR-003**: Decision points MUST NOT be connected to one another or to operational record relationship lines.
- **FR-004**: Points MUST remain individually reachable; same-position collisions MAY use the existing counted grouping with every member available.
- **FR-005**: Decision reads MUST be tenant-scoped and bounded, disclose partial loading, refresh with the timeline, and preserve prior data on refresh failure.
- **FR-006**: Order-filtered journeys MUST omit these tenant-wide points. The implementation MUST NOT inspect proposal payloads to infer order membership.
- **FR-007**: No persistence, event, authorization, confirmation, Record graph or Inspector contract changes are introduced.

## Success Criteria

- **SC-001**: Pending, accepted and rejected fixtures render the expected points with no decision connector.
- **SC-002**: The lane and points work in all supported languages and at 390px and 1440px.
- **SC-003**: Selecting an order produces zero tenant-wide decision points.

## Assumptions and Dependencies

The existing change-proposal register is the authority for decisions. `created_at`, `status` and `decided_at` are sufficient for this presentation. The owner explicitly approved unconnected points on 2026-09-26. A future explicit proposal-to-business-subject relationship may extend order journeys; payload matching is not acceptable.

## Requirement Traceability

| Requirements | Story | Tasks | Proof |
|---|---|---|---|
| FR-001–004 | US1 | T002–T004 | order-journey-layout.test.mjs, order-journey-browser.mjs |
| FR-005–007 | US1 | T003–T005 | browser bounded/error/order checks, build and spec checks |
