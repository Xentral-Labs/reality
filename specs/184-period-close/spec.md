# Feature Specification: Period Close

**Feature Branch**: `184-period-close`
**Created**: 2026-09-12
**Status**: Proposed (stub; scope to be written)
**Language**: English
**Input**: Follow-up from [Storyline mode](../182-storyline-mode/spec.md): the owner's story
closes the month and carries open findings into the next period. Research R7 of spec 182
found no period record and no close command on main.

## Context and Intent

### Problem

Reality has no notion of an accounting or operating period. Nothing marks a month as closed,
and open findings have no period they belong to or are carried into.

### Scope

To be specified: a period record per tenant, a close command that freezes the period's facts,
lists the findings still open and links them to the next period, and a closing report.

### Non-Goals

- No fiscal-year logic, no tax reporting, no ledger locking beyond what the close needs.
- No reopening in the first version.

### Existing Contracts

- [Storyline mode](../182-storyline-mode/spec.md) FR-014: version 2 of Order to close replaces
  the read chapter "Month-end review" with the close chapter.
- [Background projections](../179-background-projections/spec.md): stored projections and
  their freshness.

## User Scenarios & Testing

To be written.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST let an owner close a period, freezing the period's recorded facts, listing the findings still open at the close and linking them to the following period, without deleting or recomputing anything.

Further requirements to be written.

## Success Criteria

To be written.

## Assumptions and Dependencies

- Constitution III applies: the period record needs the scenarios in this spec before any schema.
- Constitution VIII applies: a close records nothing a source states; it freezes and links.

## Requirement Traceability

| Requirement | Evidence |
| --- | --- |
| FR-001 | to be filled by the plan and the tasks |
