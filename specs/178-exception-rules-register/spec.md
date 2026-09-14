# Feature Specification: Exception Rules Register

**Feature Branch**: `178-exception-rules-register`
**Created**: 2026-09-12
**Status**: Implemented
**Language**: English
**Input**: Owner request (German, 2026-09-12): turn the Exception rules tab into a table, show per class how many findings are currently open, list them in the row's quick preview, and give every class a column with a good description from the catalog of what it detects.

## Context and Intent

### Problem

The Exception rules tab in the Reality Inspector (spec 138, FR-029) renders the operational
exception catalog as a stack of collapsed disclosures: one label per class, everything else
hidden until a row is opened. Nothing on the page tells the reader whether a class is relevant
to their company right now. The same catalog descriptions already explain, in one paragraph
each, what a class detects and how it clears; today they are only visible one row at a time.
The Exceptions page shows the open findings but does not group them by class.

### Scope

- The Exception rules tab becomes a register table with one row per catalog class: the finding
  type, the catalog description of what it detects, the severity, and the number of findings
  currently open for that class in the selected company.
- The row's quick preview (spec 164 inline preview) lists the open findings of that class with
  the same title, context and impact the Exceptions page shows, lets the reader open the full
  explanation of a finding, and carries the full catalog description, the responsible area and
  how the class clears.
- A read-only per-class count and a per-class filter over the existing attention derivation,
  exposed through the Web API for the tenant.

### Non-Goals

- No stored counts, no new table or column: the counts and the filtered list are the same
  read-time derivation the Exceptions page pages through (Constitution rule 11).
- No change to the exception derivations, the catalog content or the Exceptions page itself.
- No translation of the catalog descriptions, responsible areas and clearing conditions; they
  keep the catalog's original language as before (spec 138). Only the class labels are shown
  in the UI language, from the ERP vocabulary the resource catalog already records.
- No MCP or CLI surface for the per-class count; agents already receive the same findings
  through the existing exception reads.
- The Exception catalog dialog opened from the Exceptions page keeps its disclosure list.

### Existing Contracts

- [Reality Inspector](../138-reality-inspector/spec.md) — FR-029 places Exception rules under Rules.
- [Inline row previews](../164-inline-row-previews/spec.md) — the preview pattern the table reuses.
- [Unified warehouse and attention](../141-unified-warehouse-attention/spec.md) — the attention register.
- [Operational exception catalog](../../packages/reality-core/config/operational_exception_catalog.yaml)

## User Scenarios & Testing

### User Story 1 - See which exception rules matter right now (Priority: P1)

An owner opens Rules → Exception rules and reads, per finding type, what it detects and how many
findings are open for it in this company, without opening anything.

**Why this priority**: This is the question the tab could not answer at all; every other part of
the change builds on the table.

**Independent Test**: Load the tab for a company with a known open finding; the row of that
class shows the catalog description and a count of at least one, every other class shows zero.

**Acceptance Scenarios**:

1. **Given** the catalog has 35 classes and the company has three open findings of one class,
   **When** the tab loads, **Then** the table lists 35 rows in catalog order, that class shows
   3 in the open column and every other class shows 0.
2. **Given** the table is shown, **When** the reader types into the search box, **Then** rows
   are filtered over label, description, responsible area and class id, and an empty result is
   reported as no matching records.
3. **Given** the open counts cannot be read, **When** the tab loads, **Then** the catalog table
   still renders, the count column shows a dash, and a retry is offered.

---

### User Story 2 - See the open findings of one class in place (Priority: P1)

The reader opens a row's preview and sees the open findings of that class with the context and
impact the Exceptions page shows, can explain one of them, and can jump to the Exceptions page
filtered to this class.

**Why this priority**: The count alone invites the question "which ones?"; answering it in place
is the owner's stated wish.

**Independent Test**: Open the preview of a class with open findings; the listed findings match
the attention register filtered to that class.

**Acceptance Scenarios**:

1. **Given** a class with three open findings, **When** its preview opens, **Then** the preview
   lists the three findings with title or context and impact, each with an Explain finding
   action that opens the finding's explanation.
2. **Given** a class with no open finding, **When** its preview opens, **Then** the preview says
   there are no open findings of this type and offers no jump to the Exceptions page.
3. **Given** a class with more open findings than the preview lists, **When** its preview opens,
   **Then** the preview shows how many of the total are listed and the Open in Exceptions action
   leads to the Exceptions page filtered to that class.
4. **Given** the preview is open, **When** the reader reads the description block, **Then** it
   carries the full catalog description, the responsible area, how the class clears, and the
   class id with its severity.

---

### User Story 3 - Read the same findings per class through the API (Priority: P2)

An integrator or the Web app asks the tenant API for the open findings per class and for the
findings of one class.

**Independent Test**: Call the summary and the class-filtered register for a company with a
known finding and compare with the unfiltered register.

**Acceptance Scenarios**:

1. **Given** a tenant, **When** the summary is read, **Then** every catalog class is listed in
   catalog order with its open count and the total equals the unfiltered register total.
2. **Given** a class id, **When** the register is read with that filter, **Then** only findings
   of that class are returned; an unknown class id is refused as an invalid request.
3. **Given** a finding clears in Reality, **When** the summary is read again, **Then** the count
   of its class has dropped without any write.

### Edge Cases

- A class in the catalog with no derivation yet reports zero rather than disappearing.
- A tenant the user cannot read returns not found for the summary, as for the register.
- The preview lists at most ten findings; the count in the column stays the true total.
- Switching companies reloads counts and closes any open preview state tied to a class.

## Requirements

### Functional Requirements

- **FR-001**: The Exception rules tab MUST render the operational exception catalog as a register
  table with one row per class in catalog order, showing finding type, the catalog description
  of what it detects, severity and the number of currently open findings of that class.
- **FR-002**: The open count MUST be derived at read time from the same operational exception
  derivation the Exceptions page uses, for the selected company only.
- **FR-003**: Each row MUST offer an inline quick preview that lists the open findings of the
  class (title or context, impact), an Explain finding action per finding, and the full catalog
  description, responsible area, how the class clears, class id and severity.
- **FR-004**: The preview MUST offer a jump to the Exceptions page filtered to the class whenever
  at least one finding is open, and MUST state when none is open.
- **FR-005**: The tenant Web API MUST expose a per-class summary (every catalog class, in catalog
  order, with its open count and the total) and a class filter on the attention register that
  refuses unknown class ids.
- **FR-006**: The search box MUST filter rows over label, description, responsible area and
  class id; an empty result MUST be reported in place.
- **FR-007**: All four UI languages MUST receive labels for the new column headings and
  preview texts. The class label MUST be shown in the UI language when the resource catalog
  records one (`labels.<language>.exceptions`), falling back to the catalog's own label; the
  exception catalog read exposes these labels per class. Descriptions stay in the catalog's
  original language.
- **FR-008**: Failure to read the open counts MUST NOT hide the catalog table; the column shows
  a placeholder and a retry is offered.

### Key Entities

- **Exception class**: a catalog entry (id, label, description, severity, owner, clears_through).
- **Open finding**: a currently derived operational exception (id, class_id, severity, title,
  impact, context, target); never stored.
- **Class summary**: the read-time count of open findings per class for one tenant.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Without opening a row, a reader can tell for every class whether the company has
  open findings of it and what the class detects.
- **SC-002**: Opening a row's preview shows the open findings of that class and the same total
  the column shows, within one read.
- **SC-003**: The summary and the class filter agree with the unfiltered attention register in
  the service and HTTP boundary tests.
- **SC-004**: The tab renders without horizontal page overflow at a 390px viewport and without
  page errors in the browser check.

## Assumptions and Dependencies

- The operational exception derivation is cheap enough to run once per summary read, as it
  already runs once per Exceptions page read.
- The Exceptions page search matches the class id, so a jump filtered by class id reaches the
  right findings without a new URL parameter.
- The preview lists the first page of ten findings; readers who need all of them use the jump.

## Requirement Traceability

| Requirement | Evidence |
| --- | --- |
| FR-001, FR-006, FR-008 | `apps/web/src/unified/ExceptionRulesRegister.tsx`; `apps/web/scripts/unified-inspector-browser.mjs` (exception rules section) |
| FR-002, FR-005 | `reality.services.attention_reads.attention_summary`, `attention_register(class_id=…)`; `tests/test_attention_reads.py`; `tests/test_unified_operations_api.py` |
| FR-003, FR-004 | `ExceptionRulesRegister.tsx` preview; browser section asserts three listed findings and the jump to `/app/attention?q=<class>` |
| FR-007 | `apps/web/src/localization.tsx` (de, nl, es); `node scripts/i18n-audit.mjs`; `reality.catalogs.load_exception_class_labels`; `tests/test_playground_api.py` (every class carries a German label); browser section asserts the German row label |
| SC-004 | focused browser run at 1440px and 390px, overflow 0, no page errors |
