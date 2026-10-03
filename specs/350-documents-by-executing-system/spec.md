# Feature Specification: Documents and Labels Come From the Executing System

**Feature Branch**: `350-documents-by-executing-system`

**Created**: 2026-10-03

**Status**: Accepted (owner decision, 2026-10-03)

**Language**: English

**Input**: Owner decision while ranking the remaining scenario gaps: Reality decides and explains;
the system that executes (ERP such as Xentral, a shipping tool, or a 3PL) produces the documents.
Journey M07 asked whether customer-prescribed delivery notes and pallet labels are out of core
scope; no document said so.

## Context and Intent

### Problem

The Business Journey Guide listed M07 (customer-prescribed delivery note or pallet label) as a
gap, although producing printed documents is not what Reality is for. Without a stated boundary
the gap looked like missing work.

### Decision

Reality does not render delivery notes, pallet labels, invoices as print layouts or other
customer-specific documents. It decides and explains what ships and what is billed; the executing
system produces the documents. When such documents come back as sources, Reality records what
they state, as for every source. This matches the operating mode in which an ERP is used as the
order, invoice and shipping tool while Reality holds the operational decisions.

### Non-Goals

- Rendering delivery notes, pallet or parcel labels, or customer-specific document layouts.
- Printing or sending documents.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An honest boundary in the Guide (Priority: P1)

As a prospect asking for a customer-prescribed delivery note, I learn that my ERP, shipping tool
or 3PL produces it and Reality records what it states.

**Independent Test**: The Guide states M07 as out of scope and cites this specification.

**Acceptance Scenarios**:

1. **Given** the Guide, **When** M07 is asked, **Then** the answer names the boundary and cites
   this specification.

### Edge Cases

- A document that comes back from the executing system as a source is recorded losslessly like any
  other source; nothing in this decision changes intake.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Business Journey Guide MUST state M07 as out of scope and cite this specification.

### Domain and Architecture Requirements

- **DR-001**: No code or schema change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: M07 is `out_of_scope`, and the coverage counts add up.

## Assumptions and Dependencies

- Follows the same boundary pattern as [spec 340](../340-accounting-boundary/spec.md).

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, SC-001 | US1 | Journey catalog and Guide tests |
| DR-001 | All | Diff review: no code change |
