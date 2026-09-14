# Feature Specification: Restore Guided Fact Rules

**Created**: 2026-09-10
**Status**: Implemented, verified and deployed locally on 2026-09-10
**Language**: English
**Input**: Restore the former guided Fact-rule editor and readable results in the new application.

## Context and Intent

### Problem

The unified Rules workbench replaced the former structured editor and source-example
journey with JSON fields. Operators can no longer comfortably configure and understand
source-supported Fact rules, although the shared services remain available.

### Scope

Restore structured authoring, nested conditions, source examples and manual evidence,
recommendations and alternative outcomes, readable definitions, simulation and execution
results, version editing, activation, disable and paginated historical replay. Retain the
current register, modal, access rules, reviewed mutations and original source values.

### Non-Goals

No new rule operators, automatic activation, inference engine, schema, service semantics,
scheduled replay, generic command execution or resurrection of the old app shell.

### Existing Contracts

Specs 106 (Reality Gap), 138 (Inspector), docs/WEB_SPEC.md, existing reality-gap services.
Historical reference: App.tsx before commit 9b8394a. The user explicitly approved the
restoration after reviewing the lost capabilities; no additional product decision remains.

## User Scenarios & Testing

### User Story 1 — Configure a rule without JSON (Priority: P1)

An owner opens a question in Fact rules, configures its source, subject, conditions,
output value and observation time, reviews the draft and saves a new version.

**Independent Test**: A nested condition with decimal and boolean values round-trips
through the form and review; saving only happens after confirmation.

**Acceptance Scenarios**:
1. Given a Fact destination, when the owner edits source/line mapping and nested
   all/any conditions, then all supported parameters can be configured with labeled controls.
2. Given an existing rule, when used as a draft, then its mappings, scopes, typed values
   and advanced configuration are preserved, and its active version remains unchanged.
3. Given invalid form values, when review is requested, then a readable error appears
   without a mutation. The dialog uses structured controls and review summaries; technical rule JSON is not shown.

### User Story 2 — Establish source evidence (Priority: P1)

An owner searches held sources, selects an example or records a manual observation,
requests a recommendation and confirms the intended destination.

**Independent Test**: Search is read-only; selecting an example prepares a confirmation
that retains source identity, field path and stated value. Recommendation and alternative
outcomes use the existing reviewed mutation path.

**Acceptance Scenarios**:
1. Given search results, when a field is selected and confirmed, then its original source
   link/value are retained and can seed the draft without silently overwriting edits.
2. Given manual evidence, when a recommendation is requested, then its actual result and
   limitations appear, and accepting/overriding requires review and explicit confirmation.
3. Given no results or failure, then an empty/error/retry state appears without invented evidence.

### User Story 3 — Understand and operate versions (Priority: P1)

An owner reads a version, simulates it, reviews warnings, activates it or replays historical
sources. Members can inspect rules but cannot mutate them.

**Independent Test**: Simulation displays counts/examples; activation and each replay batch
require confirmation. Continuation uses the returned cursor for the same rule only.

**Acceptance Scenarios**:
1. Given a simulated draft, then counts, conflicts, invalid values and example outcomes are
   readable; activation is available only for the exact successfully simulated version.
2. Given an active rule, when replay is confirmed, then batch/cumulative results and explicit
   continuation appear, with no background loop. Disable also requires confirmation.
3. Given company/rule changes, modal closure or uncertain writes, then stale results/reviews
   cannot execute in another context. A read-only member never receives enabled mutation controls.

### Edge Cases

Empty/malformed values; zero matches; missing paths; nested source/element scopes; false,
zero and decimal precision; existing normalization; unknown/failed responses; double clicks;
stale revisions; company changes during reads; mobile overflow; keyboard modal focus.

## Requirements

### Functional Requirements

- **FR-001**: Provide structured source, subject/line mapping, output/type/allowed-value and time controls.
- **FR-002**: Provide recursive all/any condition editing with existing operators, scopes and typed operands; preserve existing advanced fields without loss.
- **FR-003**: Restore source search, example selection, manual observations and explicit source links.
- **FR-004**: Restore recommendation display and reviewed acceptance/alternative destinations.
- **FR-005**: Display readable version definitions, state, execution counts and simulation counts/examples, keeping raw technical rule definitions outside the editing dialog.
- **FR-006**: Preserve new-version preparation, exact-version simulation gating, reviewed activation/disable and explicit cursor-based historical replay.
- **FR-007**: Preserve tenant isolation, owner/admin restrictions, confirmation, uncertainty lock, double-submit prevention and context reset.
- **FR-008**: Work with keyboard and narrow screens, and localize all new interface labels in en/de/nl/es; external values retain their language.

### Domain and Traceability Requirements

- **DR-001**: Keep Source → Evidence → Fact through existing opaque references; never create authority from a display derivation.
- **DR-002**: Use existing tenant-scoped application endpoints/services for every operation. No alternative rules or persistence in the browser.

### Key Entities

Existing Reality Gap, evidence/recommendation entries, versioned Fact rule, SourceRecord,
simulation and replay results. No new persisted entities.

## Success Criteria

- **SC-001**: Each of the seven audited legacy capability areas is available in the current workbench.
- **SC-002**: Ordinary rule configuration, evidence selection and result review require no JSON editing.
- **SC-003**: Every requirement has a test or browser acceptance proof; unconfirmed controls create zero mutations.

## Assumptions and Dependencies

Existing service validation remains authoritative. Historical UI is a behavioral reference;
current register/modal design and service confirmation boundaries take precedence. Local
integration worktree changes are intentional and must be preserved.

## Requirement Traceability

| Requirement | Scenario | Evidence |
|---|---|---|
| FR-001, FR-002 | US1.1–3 | guided-rule-draft.test.mjs, guided-rules-browser.mjs |
| FR-003, FR-004, DR-001 | US2.1–3 | guided-rules-browser.mjs, existing reality-gap tests |
| FR-005, FR-006 | US3.1–2 | guided-rules-browser.mjs, draft tests |
| FR-007, DR-002 | US3.3 | browser confirmation/role/context tests, shared backend suite |
| FR-008 | US1–3 | i18n audit, mobile/keyboard screenshots |

## Approved usability refinement — 2026-09-10

The owner approved a sentence preview and three clear areas: When does the rule apply,
What should be remembered, and Check with examples. Technical mapping and history are
secondary disclosures. Existing values must populate immediately on Edit. An accepted
question with no version is explicitly labeled Set up rule, not Edit rule.

- **FR-009**: Show a truthful localized sentence preview of the current form; incomplete
  drafts show prompts instead of invented behavior. Initialize an edit from the latest
  draft, otherwise active/latest version, once per selected question without overwriting edits.
- **FR-010**: Use the three approved sections, progressive all/any controls, collapsed
  evidence/history/advanced mapping, and a persistent cancel/review/confirm action bar.
  Review still precedes every write and preview never simulates unpersisted definitions.

Acceptance: opening an existing rule shows populated fields and its sentence; opening an
accepted question without versions shows Set up rule and an honest setup prompt. Zero/single
conditions hide irrelevant group mode. Advanced settings remain editable without loss.
At 390px and desktop the footer is reachable without scrolling and all existing workflows pass.

| Requirement | Scenario | Evidence |
|---|---|---|
| FR-009 | Open existing/new setup, edit without overwrite | guided-rule-draft.test.mjs, guided-rules-browser.mjs |
| FR-010 | Progressive editor and persistent review | guided-rules-browser.mjs, mobile screenshots |

## Approved example-step refinement

FR-011: Keep steps 1 and 2 unchanged. Step 3 contains source search, selected supporting evidence and saved-version simulation together. Remove technical rule JSON from the editing and confirmation UI. Put supplementary context and history under Further details. Tests must clearly describe the existing bounded source preview, without claiming that evidence selection filters simulation.

Acceptance: Opening a Fact rule exposes supporting examples inside step 3, no separate example accordion and no Technical definition control; saved-version simulation and confirmation remain available.
