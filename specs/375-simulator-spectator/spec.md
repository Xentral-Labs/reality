# Feature Specification: Simulator spectator

**Language**: English

**Feature**: 375-simulator-spectator | **Created**: 2026-10-05 | **Status**: Accepted scope

## Context and Intent

### Problem
The company simulator has readable proof files but no accessible way to watch customer correspondence, supplier activity and business progress together.

### Scope
A separate local, read-only spectator shows saved and active simulator runs. It displays original recorded messages, related accepted actions, a company timeline and checkpoint results. It belongs to the simulator, independently of Reality's product UI.

### Non-Goals
No business mutations or simulator execution start/pause/resume controls, real email transport, invented replies, complete correspondence simulation, provider connection, production dashboard or multi-day runtime infrastructure. Existing supplier actions must never be presented as sent emails. No business schema changes.

## User Scenarios & Testing

### User Story 1 - Watch the company (Priority: P1)
Select a saved or active run and understand what happened in the business and whether the last independent check passed.

**Independent Test**: A saved prompt run shows its simulated day, recorded core outcome, stock, goals and chronological business activity. An unfinished run shows its latest checkpoint without claiming completion or that its process is alive.

**Acceptance Scenarios**:
1. Given a completed run, selecting it shows its timeline, planned/exercised case-family counts, goal outcomes and exact recorded checkpoint totals.
2. Given a growing journal, refreshing shows new complete records; a trailing incomplete write leaves earlier records visible with a notice.
3. Given a failed checkpoint, expected/actual differences are visible separately from missed customer delivery goals.

### User Story 2 - Follow customers and suppliers (Priority: P1)
Choose a customer or supplier and inspect their correspondence and related business actions.

**Independent Test**: Two customer threads and a supplier purchase are explicitly linked to their recorded party IDs; an absent response has an empty state.

**Acceptance Scenarios**:
1. A customer order message shows its original sender, recipient, subject, body, simulated day and source ID. Its accepted order/dispatch actions are distinguishable from messages.
2. Supplier orders and receipts appear as actions in the supplier view; no supplier email is fabricated.
3. If a journal contains an outgoing message, its recorded proposed/approved/simulated-sent state is displayed without inferring approval or delivery. Legacy messages with no recorded state are labelled as such.

### Edge Cases
Empty root; unknown run; unreadable/malformed journal; partial final line; stale unfinished run; missing old live snapshot; unknown party reference; malicious message text; path traversal/symlink outside configured root; changed selected run during refresh.

## Requirements

- **FR-001**: List eligible runs from one explicitly configured local artifact root and allow selecting one without a database or owner token.
- **FR-002**: Show customer and supplier views linked using explicit recorded party/source/order references. Unresolvable correspondence remains visibly unassigned.
- **FR-003**: Render original message fields and optional recorded direction/status as plain text. Distinguish messages from accepted business actions and pending proposals; never invent replies or infer email sent/approval from business action acceptance.
- **FR-004**: Present a chronological business timeline with simulated days, named business actions, retained trace references and expandable original evidence. Exclude technical prepare/commit duplication from business-event counts.
- **FR-005**: Display the last checkpoint's recorded stock, financial observations and differences; completed reports supply goal and planned/exercised coverage counts. No checkpoint means unchecked. Unfinished status means no final report, not verified process liveness.
- **FR-006**: Refresh active/saved data within ten seconds while preserving run/party selection. Completed records remain available despite a trailing incomplete journal record; malformed complete records and missing artifacts produce visible notices.
- **FR-007**: New complete/Shopify runs publish atomic read-only spectator snapshots after checkpoints and at terminal outcomes, with only released world activity and retained actual references. Snapshot export never changes business results or operator visibility.
- **FR-008**: Serve only on loopback, with read-only routes restricted to known artifact filenames and runs beneath the configured root. Reject traversal and symlink escapes. No product UI modifications or new external frontend dependencies.
- **FR-009**: Provide a responsive local webpage with keyboard-accessible navigation, readable empty/error states, and English repository/UI copy.

### Key Entities
Run artifact set; original message; explicit business party; recorded business event; checkpoint; derived spectator response. All are run-local observations, not new business authority.

## Success Criteria
- **SC-001**: A completed reference month exposes all ten recorded order messages, supplier actions and independently verified closing numbers without reading raw JSON.
- **SC-002**: An additional complete journal event appears within ten seconds; partial writes do not remove previous visible records.
- **SC-003**: Customer/supplier filtering and switching runs never mix records across runs; hostile text stays inert.
- **SC-004**: Viewer reads leave all source artifacts unchanged and require no database connection.

## Assumptions and Dependencies
- Repository content, including viewer copy and tests, is English.
- User accepted the proposed separate local spectator in this conversation. The complete profile now records local customer/supplier correspondence under spec374 FR-009; this viewer exposes only recorded evidence and labels simulated responses and unsent drafts explicitly.
- Specs 373/374 artifact journals and normal application tools remain authoritative. UI polling is read-only presentation, not business scheduling.
- Local artifact directories are trusted simulator outputs. This is a loopback development viewer, not an authenticated multi-user deployment.
- The finite simulator may finish quickly; saved-run viewing is equally important. Real-time pacing and durable process resume are not added.

## Requirement Traceability

| Requirement | Tests | Implementation |
| --- | --- | --- |
| FR-001 | test_simulator_viewer + browser_check | ArtifactStore, server, run selector |
| FR-002 | explicit_customer_supplier + identity regression + browser_check | Accepted source context and party filters |
| FR-003 | original_outgoing_state + browser_check | Plain-text messages, recorded state, separate actions |
| FR-004 | explicit_customer_supplier + browser_check | World timeline and original evidence |
| FR-005 | partial_tail + snapshot_outcome + browser_check | Captured checkpoints/goals/coverage |
| FR-006 | partial_tail + browser_check | Five-second selected-run refresh, notices |
| FR-007 | test_complete_company snapshot assertions and export-failure proof | CompanyRun.publish_spectator |
| FR-008 | paths_and_symlinks + http_read_only_routes | Loopback server and artifact allowlist |
| FR-009 | browser_check narrow viewport/filtering | Separate responsive static viewer |

## Live and replay story presentation

- **FR-010**: The company story surface explicitly separates watching journal updates from replaying saved days. Watching polls every five seconds and follows the newest available checkpoint; replay controls only presentation and never start, pause or modify simulator execution. Preserve selected run and story, show observation age and incomplete-write notices, and do not claim process liveness. Replay uses only checkpoints actually present. Unsupported profiles show an explicit fallback to the original spectator.
- Acceptance: append a checkpoint to a selected run and see the new day in watch mode; switch to replay and keep its day while updates arrive; switch runs without a stale fetch mixing them. Missing checkpoints and fetch errors remain visible. Play/pause issue no mutation requests.

FR-010 traceability: `test_story_data_keeps_complete_checkpoints_and_safe_paths`, `stories_browser_check.cjs` → `ArtifactStore.story_data`, fixed story assets and read-only story endpoint.

## Live-runtime scope handoff

The approved sustained external-agent and simulated-mailbox direction is specified in [spec376](../376-live-company-simulator/spec.md), including manual preview/injection. This specification's finite-run/viewer implementation is baseline evidence, not proof of continuous pacing, durable resume or external-agent inbox integration. Those remain pending; do not label the current PR a complete live runtime.
