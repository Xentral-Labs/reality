# Feature Specification: Saving an analysis is visible and named

**Feature Branch**: `261-analytics-save-clarity`
**Language**: English
**Created**: 2026-09-23
**Status**: Approved
**Input**: Owner, after creating reports in Analytics for the first time: a template is understandable, but nothing says that an adopted template has to be saved to become a report, and the name has to be invented from nothing. Review how a report is created by chat, from a template and by hand, and fix what is not intuitive.

## Context and Intent

### Problem

Analytics saves the question, never its answer, and that is the right model. What is missing is the moment a person turns a question into a report of their own. Four things hide it:

1. **The save action is not on the page.** `Save` renders through `PageActionBar`, which portals its buttons into the page header, where `RegisterActions` collapses them into a generic "More actions" menu. Next to the analysis there is no save control at all. The same is true for "New analysis" in the report library and "Use in analysis" in the data catalog: every primary action of the module sits behind one unlabelled menu.
2. **The name starts empty.** The naming field opens blank and the backend refuses an empty name, so a person must invent one at the moment they least want to. A template already carries a label and the copilot already proposes a name; neither reaches the field.
3. **Nothing says the analysis is unsaved.** Adopting a template replaces the template list with the builder under the heading "How Reality understands your question". The template's name is dropped at the call site. There is no visible difference between a saved report and a draft, so the step that has to happen next is invisible.
4. **Confirming in chat leads back to an unsaved copy.** After a proposal is confirmed, its card still offers "Open in analysis", which opens the proposal's *definition* as a fresh draft with no report identity. A person who then saves creates a duplicate of the report they just confirmed. The proposal read model cannot do better today: for a create it has no way to name the row that was written.

Two smaller defects belong to the same journey. In German `"Use a template"` and `"Use template"` are both "Vorlage verwenden", so the toggle and the row action are indistinguishable. And a template advertises a living window ("Comes with a period: this month") while adoption resolves it to fixed instants, which the library's "Each opening runs against current records" reinforces.

### Principle

A question becomes a report at one visible moment, by one visible action, under a name the system already knows how to propose. Saving stays explicit — nothing is written without a person asking — but the ask must be in front of them, pre-filled and reversible, not hidden in a menu and blank when found.

A proposed name is a suggestion, never an authority: it is selected on open so one keystroke replaces it, and it is never written without the person confirming.

### Scope

The Analytics surface (`apps/web/src/unified/AnalyticsPage.tsx`, `analytics/`), its German wording, and one read-model addition so a confirmed proposal can name the report it created.

### Non-Goals

No autosave and no change to when a report is written. No change to the stored question, the traversal model, the compiler, or what a report answers. No shared or company-wide reports — a report stays private to its author. No new report field: the created row is found through the retry key it already records. No redesign of the builder's sentence, filters or result table. No change to the copilot's naming behaviour beyond carrying the name it already proposes into the confirmation and the report.

## User Scenarios & Testing

### User Story 1 — Save is where the analysis is (Priority: P1)

A person who has an answer in front of them can see how to keep it.

**Why this priority**: This is the reported failure. Without it the other stories have no entry point.

**Independent Test**: Open Analytics, build or adopt any analysis, and observe a save control without opening any menu.

**Acceptance Scenarios**:

1. **Given** an executed analysis, **When** it is shown, **Then** a "Save analysis" button is visible next to it without opening a menu, and it is the primary action.
2. **Given** a saved report is open, **When** it is shown, **Then** the visible primary action is `Save "<name>"` and "Save as a new report" is offered beside it.
3. **Given** the report library, **When** it is shown, **Then** "New analysis" is visible without opening a menu.
4. **Given** the data catalog, **When** an object is selected, **Then** "Use in analysis" is visible without opening a menu.
5. **Given** the save control is pressed, **When** the name field appears, **Then** it appears in the same place as the control that was pressed, focused.

### User Story 2 — The name is already there (Priority: P1)

A person saving an analysis is offered a name that describes it and can accept it unchanged.

**Why this priority**: The second half of the reported failure; it is what turns saving from a decision into a confirmation.

**Independent Test**: Reach the naming field from each of the three origins and observe a non-empty, sensible, editable suggestion.

**Acceptance Scenarios**:

1. **Given** a template was adopted, **When** the name field opens, **Then** it holds the template's label, selected.
2. **Given** an analysis built by hand or started from the data catalog, **When** the name field opens, **Then** it holds a name derived from the analysis itself — its records, its measures and what it is grouped by, in the reader's language — selected.
3. **Given** a suggested name, **When** the person types, **Then** the first keystroke replaces the whole suggestion.
4. **Given** the suggestion is accepted unchanged twice, **When** the second save is confirmed, **Then** it is accepted and the two reports are distinguishable by the library's existing name, updated time and rename action. Names are not required to be unique.
5. **Given** a name field, **When** it is emptied, **Then** the save control is disabled and no request is sent.

### User Story 3 — A draft looks like a draft (Priority: P2)

A person can always tell whether what they are looking at is a saved report or an unsaved question, and which report it is.

**Why this priority**: It explains why the save action is there, and it is what makes an adopted template legible.

**Independent Test**: Adopt a template, then open a saved report, and compare the heading in both.

**Acceptance Scenarios**:

1. **Given** an adopted template, **When** the builder is shown, **Then** it carries the template's name and states that it is not saved yet.
2. **Given** an analysis built by hand, **When** the builder is shown, **Then** it states that it is a draft that is not saved yet.
3. **Given** a saved report is open, **When** it is shown, **Then** it carries the report's name and no draft notice.
4. **Given** a saved report whose question was then changed, **When** it is shown, **Then** it carries the report's name and states that there are unsaved changes.

### User Story 4 — Saving lands somewhere (Priority: P2)

After saving, a person knows it happened, is looking at the saved report, and can get to their library.

**Why this priority**: Without it a saved report is indistinguishable from an unsaved one and a reload silently loses the connection.

**Independent Test**: Save an analysis, read the confirmation, reload the browser, and confirm the same saved report is still open.

**Acceptance Scenarios**:

1. **Given** a save succeeds, **When** the response arrives, **Then** the analysis is shown as that saved report, with a stated confirmation and a link to "My reports".
2. **Given** a save succeeds, **When** the address is reloaded, **Then** the same saved report opens.
3. **Given** the question is changed after saving, **When** the change is executed, **Then** the confirmation is gone and the unsaved-changes state of US3 applies.
4. **Given** a save fails, **When** the failure arrives, **Then** the reason is shown, the entered name is kept, and nothing about the analysis is lost.

### User Story 5 — A confirmed proposal opens the report it created (Priority: P2)

A person who asked the copilot for a report and confirmed it is taken to that report, not to a copy of it.

**Why this priority**: Today this path silently produces duplicates, which is worse than an unclear one.

**Independent Test**: Ask the copilot for a report in chat, confirm the proposal, and follow the button on the card.

**Acceptance Scenarios**:

1. **Given** a confirmed create proposal, **When** its card is shown, **Then** it states that the report was saved and offers to open the saved report.
2. **Given** that button, **When** it is followed, **Then** the saved report opens with its name and its save state, not as a draft.
3. **Given** a proposal that is still awaiting confirmation, **When** its card is shown, **Then** it offers "Open in analysis" as today, and what opens is stated to be an unsaved preview of the proposal.
4. **Given** a confirmed update, rename or duplicate proposal, **When** its card is shown, **Then** it offers to open the report the change applies to.
5. **Given** a rejected proposal, **When** its card is shown, **Then** it offers no way to open a report.

### User Story 6 — The words say what happens (Priority: P3)

**Why this priority**: Cheap, and both items actively mislead today.

**Independent Test**: Read the template list in German, adopt a template with a period, and read the filter.

**Acceptance Scenarios**:

1. **Given** the German edition, **When** the analysis choice screen and the template list are shown, **Then** the toggle and the per-template action read differently.
2. **Given** a template with a period, **When** it is shown, **Then** it states the window it will set and that adoption fixes it to dates.
3. **Given** an adopted template with a period, **When** the filter is shown, **Then** it names the resolved dates, as today.

### Edge Cases

- A question the builder cannot represent (expert clauses) still saves: the save control stays available whenever an answer exists, and the name is suggested from the stored question's root records where the plan is unavailable.
- A template with a snapshot date keeps its existing gate: the action stays disabled until a date is chosen.
- Two people, or two tabs, saving the same suggested name both succeed; names are not unique and never were.
- A confirmed create whose row was later deleted: the card states the report is no longer available and offers no open action.
- A proposal sealed with a key this installation no longer has stays rejectable only, as today.
- The library's rename dialog is unchanged and keeps starting from the current name.

## Requirements

### Functional Requirements

- **FR-001**: Analytics presents its primary actions on the page, not in the header's "More actions" menu: the save controls beside the analysis, "New analysis" in the report library, and "Use in analysis" in the data catalog. The existing inline presentation of `PageActionBar` is used; no new action mechanism is added.
- **FR-002**: The naming field opens in the same place as the control that opened it, focused, with its suggested value selected.
- **FR-003**: A save opened from an adopted template suggests the template's label. The template's label is carried from the template list to the builder.
- **FR-004**: A save opened from an analysis with no name of its own suggests a name derived from the analysis in the reader's language: the records it reads, the measures it reports and what it groups by, from the same catalog labels the builder already shows. The suggestion is at most 120 characters, the stored limit.
- **FR-005**: A suggested name is editable and replaced by the first keystroke. An empty or whitespace-only name disables the save control; no request is sent.
- **FR-006**: The builder states which report it is showing and whether it is saved: a saved report by name; a saved report with an executed change as having unsaved changes; anything else as a draft, by its carried name where it has one.
- **FR-007**: A successful save shows the analysis as the saved report, records the report in the address so a reload reopens it, states that it was saved, and offers a link to "My reports". The statement is withdrawn as soon as the question changes.
- **FR-008**: A failed save keeps the entered name and the analysis, and states the reason.
- **FR-009**: A private report proposal's preview names the report the change concerns: the report it changes for an existing-report operation, and for a confirmed create or duplicate the row written under that change's retry key. No field is added to the report; the existing `create_request_id` is the link.
- **FR-010**: The chat proposal card distinguishes its states. Awaiting confirmation it offers "Open in analysis" and states that this is an unsaved preview of the proposal. Confirmed, it states that the report was saved and offers to open the saved report, which opens it as a saved report. Rejected, or when the named report no longer exists, it offers no open action.
- **FR-011**: The German edition distinguishes the template toggle from the per-template action.
- **FR-012**: A template with a period states the window it sets and that adopting it fixes that window to dates. The resolved dates continue to be shown in the adopted filter.

## Key Entities

No new entity, column or migration. `AnalyticsReport.create_request_id` — already written and already unique per author — is read to resolve a confirmed create proposal to its report.

## Success Criteria

### Measurable Outcomes

- **SC-001**: From an executed analysis, saving it under a usable name takes one click to open the field and one to confirm, with no menu opened and no name typed.
- **SC-002**: Each of the three origins — chat, template, by hand — arrives at a non-empty suggested name.
- **SC-003**: Confirming a report proposal in chat and following the card's button opens the saved report; the number of reports does not increase on that path.
- **SC-004**: Reloading the browser on a just-saved analysis reopens the same saved report.
- **SC-005**: No new endpoint, service, table or column; the read model gains one resolved field.

## Assumptions and Dependencies

- Builds on spec 238 (public analytics model), spec 236 (requested analysis) and the existing private-report proposal sealing. Nothing about the sealed payload or the confirmation boundary changes.
- Names are not unique and are not made unique here; the library already distinguishes reports by updated time and offers rename.
- `PageActionBar` already supports an inline presentation, so FR-001 is a presentation choice at the call sites, not new shared machinery. Whether a page keeps a "More actions" menu for its secondary actions is decided per call site.
- Reports stay private to their author, so a suggested name never leaks another person's wording.
- The resolution of a template's named window into absolute instants is deliberate (a stored question holds instants) and is not changed; only what the surface claims about it is corrected.

## Requirement Traceability

FR-001, FR-002 → US1. FR-003, FR-004, FR-005 → US2. FR-006 → US3. FR-007, FR-008 → US4. FR-009, FR-010 → US5. FR-011, FR-012 → US6.

Verified by `packages/reality-core/tests/test_analytics_report_proposals.py` (FR-009), `apps/web/scripts/analytics-report-naming.test.mjs` (FR-003 – FR-006), `apps/web/scripts/analytics-save-clarity-browser.mjs` (US1 – US6 in the browser), the frontend build and `npm run i18n:audit` (FR-011, FR-012).
