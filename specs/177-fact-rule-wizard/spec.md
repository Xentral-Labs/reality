# Feature Specification: First-Time Fact Rule Wizard

**Created**: 2026-09-12
**Status**: Implemented and verified on 2026-09-12; scope approved by the owner
**Language**: English
**Input**: Make creating a new Fact rule intuitive through a guided wizard, because the current business question and intended use form does not explain what to do.

## Context and Intent

### Problem

New rule currently opens two unexplained fields and Review change. Confirming creates
an open question, not a rule. Source evidence, interpretation, configuration, draft
saving, simulation and activation follow without an understandable overall journey.
An operator cannot tell what to enter, what a good rule looks like or when it takes effect.

### Scope

Provide a continuous first-time authoring wizard in the existing modal, with five
visible stages, one current stage, plain-language guidance and contextual examples:

1. **Choose a goal** — Explain that a Fact rule remembers a source-supported property
   about an existing business record. Offer editable starters such as retaining a
   delivery instruction or classifying an order from an explicit source field, plus
   a custom goal. Ask what to remember and what decision it helps with. Show filled
   examples beside these questions. Review and confirm recording the question before
   the first durable write, clearly explaining that no rule is active yet.
2. **Find a real example** — Search held source records and select an original field
   and value. Explain why evidence is needed and link to the source. Guide the user
   through attaching evidence, requesting a recommendation and reviewing its actual
   result. A non-Fact outcome receives a truthful explanation and existing handoff,
   rather than being forced into a Fact rule.
3. **Describe the rule** — Configure when it applies and what it remembers using the
   existing supported source, subject, conditions and output controls. Show a live
   sentence describing the current selections. Put technical mappings and advanced
   options behind contextual disclosures. Review and explicitly save the draft to
   make it available for testing.
4. **Test with existing data** — Simulate the exact saved version. Explain matches,
   expected Facts, skipped records, invalid values and conflicts using the actual
   results. Distinguish the selected supporting example from the bounded simulation
   sample. Offer a clear return to correct the draft and then save and test again.
5. **Review and activate** — Summarize the rule, source, subject, result and tested
   version. Explain that activation applies to future matching intake and historical
   replay is separate. Explicitly confirm activation and show the returned status.

Persisted milestones remain visible if the user stops. Each stage names its next
action and any reason it cannot proceed. Existing rule editing and version operations
remain available with their established behavior.

### Non-Goals

- No new rule engine, operators, subject capabilities, schemas or automatic AI rule generation.
- No automatic activation, historical replay or business actions triggered by wizard navigation.
- No replacement of the existing reviewed mutation boundaries with a silent multi-write workflow.
- No redesign of the rules register or of existing rule version management.
- No promise that every manually observed Fact predicate supports source-rule extraction.

### Existing Contracts

- [Guided Fact rules](../159-guided-fact-rules/spec.md)
- [Web product contract](../../docs/WEB_SPEC.md)
- [Reality gaps and safe Fact rules](../../docs/features/reality_gaps.md)
- [Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing

### User Story 1 - Understand and start a useful rule (Priority: P1)

An operator sees what a Fact rule does, chooses an editable example and describes
their own goal without knowing the term Reality Gap.

**Why this priority**: Fixes the unexplained entry screen in the reported screenshot.

**Independent Test**: Open New rule, select and edit a starter, navigate back and
forward, then review the first write without creating an active rule.

**Acceptance Scenarios**:

1. **Given** New rule is opened, **When** the first stage appears, **Then** the user
   sees an explanation, editable starters, five-stage progress and one primary action.
2. **Given** a selected starter, **When** the user edits its goal or purpose and
   navigates backward, **Then** their edits remain and no business write occurs.
3. **Given** missing required input, **When** the user tries to advance, **Then** an
   inline explanation identifies what is needed and focus reaches the invalid input.
4. **Given** valid input, **When** the user confirms recording the question,
   **Then** the next stage explains the saved milestone and no active-rule claim appears.

### User Story 2 - Build from evidence and see what the rule means (Priority: P1)

An owner selects an actual source value and configures a supported rule while reading
its meaning as an ordinary sentence.

**Why this priority**: A welcoming first screen is insufficient if the next step is opaque.

**Independent Test**: Complete evidence and interpretation with existing confirmation
boundaries, configure a rule and review its saved draft.

**Acceptance Scenarios**:

1. **Given** an existing source example, **When** its field is selected and confirmed,
   **Then** the original value and source link remain visible and supported draft
   suggestions do not overwrite subsequent user edits.
2. **Given** no examples, unavailable data or a non-Fact recommendation, **When** the
   result appears, **Then** the user sees an explanation and applicable retry,
   alternative search or existing manual-observation/handoff action without fabricated evidence.
3. **Given** configured conditions and output, **When** the draft changes, **Then**
   the sentence reflects those settings, incomplete parts remain explicit and saving
   requires review and confirmation. Advanced fields retain their existing values.

### User Story 3 - Test, activate or leave safely (Priority: P1)

An owner understands the actual test result and deliberately activates the tested
version, or leaves with an accurately described saved milestone.

**Why this priority**: Prevents confusion between recording a question and enabling a rule.

**Independent Test**: Save, simulate, revise, re-save, re-simulate and activate; check
closing, failure and company changes at every durable milestone.

**Acceptance Scenarios**:

1. **Given** a saved draft, **When** simulation completes, **Then** actual counts,
   sample bounds and problems appear; the selected evidence is not presented as the
   simulation filter and zero matches are not described as successful coverage.
2. **Given** tested version A, **When** the draft is edited, **Then** the wizard
   requires saving and testing the revision before its activation can be reviewed.
3. **Given** the current saved version has passed existing activation prerequisites,
   **When** activation is confirmed, **Then** the returned status appears and historical
   records are not replayed automatically.
4. **Given** any stage, **When** the user exits, **Then** nothing pending executes,
   persisted milestones remain inspectable and unsaved changes are not called saved.
5. **Given** a read-only member, company switch, double click, stale revision or
   uncertain write response, **When** navigation or submission occurs, **Then** the
   existing permission, context isolation, duplicate prevention and uncertainty guards hold.
6. **Given** a narrow viewport or keyboard-only navigation in any supported language,
   **When** the wizard is used, **Then** stage headings, errors, progress and primary
   actions are readable and reachable, with focus restored when the dialog closes.

### Edge Cases

- No source records; no candidate fields; unsupported subject mapping; manual evidence only.
- Original false, zero and precise decimal values; missing paths and ambiguous subjects.
- Leaving after question/evidence/draft persistence; reopening incomplete setup; unknown writes.
- Stale simulation after editing; zero matches; conflicts; failed activation; repeated clicks.
- Tenant or rule changes during reads; long source labels; mobile scrolling; existing-rule editing.

## Requirements

### Functional Requirements

- **FR-001**: New rule MUST open the five-stage journey with one current stage,
  descriptive progress, Back and an action naming the actual next operation.
- **FR-002**: The goal stage MUST explain Fact rules with editable illustrative
  starters and contextual goal/purpose examples. Starters MUST NOT invent held sources
  or promise support beyond existing rule capabilities.
- **FR-003**: Navigation MUST preserve entered values within the current wizard,
  identify missing prerequisites inline and perform no implicit mutations.
- **FR-004**: Evidence and interpretation MUST guide selection of held source values,
  display real recommendations and provide honest empty, error and non-Fact outcomes.
- **FR-005**: Configuration MUST expose existing structured controls, a truthful
  sentence and progressive advanced options, preserving existing mappings without loss.
- **FR-006**: Testing MUST use a saved version, expose actual bounded results and
  require a newly saved and tested version after revisions before activation review.
- **FR-007**: Each durable operation MUST retain its existing review/confirmation
  boundary with readable content and an action-specific confirmation label. Activation
  MUST explain future scope and separate historical replay.
- **FR-008**: Exit and reopening MUST describe actual saved milestones; opening an
  incomplete question MUST continue setup at the earliest unmet prerequisite without
  implying unsaved inputs survived closing or performing duplicate writes.
- **FR-009**: Owner/admin permissions, uncertainty lock, tenant isolation, stale-result
  rejection and double-submit prevention MUST remain effective throughout the wizard.
- **FR-010**: All new interface copy MUST support en/de/nl/es; original values remain
  unchanged. Keyboard focus, modal exit and reachable actions MUST work at 390px and desktop.
- **FR-011**: Existing rule editing, advanced settings, disable and explicit replay
  MUST remain available with the existing version and confirmation semantics.

### Domain and Traceability Requirements

- **DR-001**: Rule-created Facts MUST retain existing source, subject and rule-version
  traceability; examples and sentence previews MUST NOT become authoritative Facts.
- **DR-002**: Every operation MUST use the existing tenant-scoped application services;
  the wizard MUST NOT introduce separate business rules, persisted entities or relationships.

### Key Entities

Existing open question, evidence, recommendation, decision, rule version, source record,
simulation and Fact. Wizard progress describes existing milestones, not a new authority.

## Success Criteria

- **SC-001**: A first-time operator can complete the supported source-backed example
  from New rule to deliberate activation without JSON editing or leaving the guided journey.
- **SC-002**: Every stage states what the user must do next; no empty required field
  prevents progress without an explanation.
- **SC-003**: Navigation alone creates zero writes; activation always identifies the
  exact reviewed, saved and tested version.
- **SC-004**: Every FR and DR has an acceptance scenario and executable proof before completion.

## Assumptions and Dependencies

- The owner accepted this concrete journey on 2026-09-12 before technical planning.
- Existing source search, recommendations, draft preparation, simulation and activation
  provide the needed capabilities; their validation and confirmation remain authoritative.
- The simple path targets existing supported Commitment and DocumentLine mappings;
  the manually observed Fact catalog does not expand rule subject support.
- Several durable reviews may be needed within a stage; progress must explain them
  instead of presenting each as an unrelated workflow.
- Existing completed-rule editing keeps the editor from spec 159.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-002, FR-003 | US1.1–4 | Wizard entry, starter, validation and navigation browser tests |
| FR-004, DR-001 | US2.1–2 | Source evidence, original values and alternative outcome tests |
| FR-005 | US2.3 | Draft round-trip, sentence and advanced field regression tests |
| FR-006, FR-007 | US3.1–3 | Version-specific simulation and confirmed activation tests |
| FR-008 | US3.4 | Exit and saved-milestone resumption tests |
| FR-009, DR-002 | US3.5 | Role, tenant, stale-response, duplicate and uncertain-write tests |
| FR-010 | US3.6 | Four-language audit and desktop/mobile keyboard browser checks |
| FR-011 | US2.3, US3.3–5 | Existing guided-rule editing and replay regression suite |

## Caret spacing regression — 2026-09-12

FR-010 readability includes vertical inset for multiline goal-purpose entry. Restore
at least 10px padding above/below text and a height of at least 60px for the two-line
purpose control. The browser regression measures the actual rendered padding/height;
no application behavior or domain contract changes.
