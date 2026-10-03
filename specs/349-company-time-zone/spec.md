# Feature Specification: Company Time Zone

**Feature Branch**: `349-company-time-zone`

**Created**: 2026-10-03

**Status**: Accepted (owner decision, 2026-10-03)

**Language**: English

**Input**: Round 4 of the scenario gaps. The owner asked for the small important gaps to be
closed ("ja mach die fünf plus M07 bis grün"); Q05 ("Time zones: order at 23:30 in New York —
stored in UTC, dated correctly?") was partial: instants are stored in UTC, but there is no
company time zone, so a late-evening local order can fall on the wrong business day.

## Context and Intent

### Problem

Reality stores every instant in UTC and turns instants into days with their UTC date. For a
company in Berlin, an order placed at 00:30 on 1 November is dated 31 October; for a company in
New York, an order placed at 23:30 on 31 October is dated 1 November. Due dates turn overdue at
UTC midnight, and a register filtered to a day shows the UTC day.

### Decision

A company states the time zone its business days are counted in (an IANA name). One shared rule
turns a value into a business day:

- a stated day — a date, date-only text, or a moment at exactly midnight UTC, which is how a
  stated day travels inside Reality — keeps its day in every zone;
- an instant is converted to the company's zone and takes that local day.

Storage stays in UTC. The rule is used wherever Reality derives a day from an instant: documents
dated by their posting or their source time, overdue days and the aging register, discount and
expiry deadlines, payment-run and opening-cutover days, register day filters, and the moment a
day-based verdict next changes (the local midnight).

## Clarifications

### Session 2026-10-03

The owner delegated these decisions to the recommended options.

- Q: What is the default for a company that states no zone? → A: UTC. That is how every day was
  counted before, so nothing an existing company sees moves until it states its zone; a German
  company states Europe/Berlin once.
- Q: Can the zone be restated later? → A: Yes, reviewed and versioned. Days already stored on
  documents stay as they were stated; only days derived at read time follow the new zone.
- Q: How is a stated day told from an instant? → A: By its form: a date or date-only text, and
  a moment at exactly midnight UTC (how stated days travel internally), keep their day.
- Q: Which day computations move to the company's zone? → A: Business days derived from
  instants in operational services and registers. Analysis reports, cost and contribution
  economic dates, synthetic demo fixtures and display-only formatting keep the UTC day and are
  named as limitations.
- Q: Is there a screen to state it? → A: Not in this increment: it is stated through Chat/MCP,
  the CLI and the web API, and confirmed by a person.

### Non-Goals

- Per-location or per-user time zones; local business hours or cut-off times.
- Converting stored document dates when the zone changes.
- Grouping analysis reports by the local day.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A late-evening order is dated on the company's day (Priority: P1)

As a merchant in New York, I want an order placed at 23:30 my time to belong to that day.

**Independent Test**: A shop order at 23:30 New York time is dated that day once the zone is stated.

**Acceptance Scenarios**:

1. **Given** a company that states America/New_York, **When** a shop order created at 23:30 on
   31 October New York time is interpreted, **Then** its instant is stored as 03:30 UTC on
   1 November and it is dated 31 October; without a stated zone it is dated 1 November.
2. **Given** a Berlin company, **When** orders at 23:30 on 31 October and 00:30 on 1 November
   Berlin time are interpreted, **Then** they are dated 31 October and 1 November.

### User Story 2 - Due dates and day filters follow the company's day (Priority: P1)

As a credit controller in Berlin, I want an invoice due today to turn overdue at my midnight.

**Acceptance Scenarios**:

1. **Given** an invoice due 31 October, **When** the aging is read at 23:30 UTC on 31 October,
   **Then** a UTC company shows nothing overdue and a Berlin company shows one day overdue.
2. **Given** a payment recorded at that moment, **Then** it is dated 1 November in Berlin.
3. **Given** a receipt at 23:30 UTC on 31 October, **When** the movement register is filtered
   to 1 November, **Then** a Berlin company lists it and a UTC company does not.
4. **Given** that invoice read earlier that day, **When** the next moment a verdict can change is
   asked, **Then** it is midnight in Berlin (23:00 UTC).

### Edge Cases

- Daylight saving: the local midnight is 23:00 UTC in winter time and 22:00 UTC in summer time.
- A stated day (a due date, a document date) never moves, also west of UTC.
- An unknown zone or an offset such as +01:00 is refused; a review that saw another zone is refused.
- Another company keeps its own zone.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A company MUST be able to state its time zone through the reviewed tool shared by
  Chat/MCP, CLI and the web API; UTC applies until it does.
- **FR-002**: Every business day Reality derives from an instant in operational services MUST be
  the company's local day, and a stated day MUST keep its day.
- **FR-003**: Register day filters MUST select by the company's local day.
- **FR-004**: The moment a day-based verdict next changes MUST be the company's local midnight.
- **FR-005**: The Business Journey Guide MUST promote Q05 with executable evidence.

### Domain and Architecture Requirements

- **DR-001**: One typed table `company_time_zone` per company, read on every day derivation and
  justified by that repeated use (Constitution III); instants stay in UTC.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Q05 is `supported`, and no existing company's derived days change until it states a zone.

## Assumptions and Dependencies

- Builds on the stated-statement pattern of the company currency (specs 309, 320).
- Analysis reports (`services/analytics/compile_sql`) keep grouping by the UTC day; changing
  that is a separate analytics design.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US1 | `tests/test_company_time_zone.py` (state, refusals, agent and person) |
| FR-002 | US1, US2.1–2 | `tests/scenarios/test_catalog_time.py`, `tests/test_company_time_zone.py` |
| FR-003 | US2.3 | `tests/test_company_time_zone.py::test_a_register_day_filter_uses_the_companys_day` |
| FR-004 | US2.4 | `tests/test_company_time_zone.py::test_the_next_clock_moment_is_the_local_midnight` |
| FR-005, SC-001 | US1 | Journey catalog Q05; existing suites unchanged with the UTC default |
| DR-001 | All | `tests/test_company_time_zone_migration.py` |
