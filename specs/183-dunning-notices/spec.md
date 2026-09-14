# Feature Specification: Dunning Notices

**Feature Branch**: `183-dunning-notices`
**Created**: 2026-09-12
**Status**: Proposed (stub; scope to be written)
**Language**: English
**Input**: Follow-up from [Storyline mode](../182-storyline-mode/spec.md): the owner's story
dunns an overdue invoice before the customer pays. Research R7 of spec 182 found no dunning
command, document or event on main.

## Context and Intent

### Problem

An overdue receivable is visible as a finding, but nothing records that the company reminded
the customer, at which level, and when.

### Scope

To be specified: a dunning notice as a document tied to one or more overdue invoices, its
level, a business event, and its appearance in the open items register and the Storyline.

### Non-Goals

- No automatic dunning runs and no fees in the first version.
- No letter delivery; the notice is a record and a document, not an email.

### Existing Contracts

- [Storyline mode](../182-storyline-mode/spec.md) FR-014: version 2 of Order to close replaces
  the read chapter "Explain the block" with the dunning chapter.

## User Scenarios & Testing

To be written.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST record a dunning notice as a document linked to one or more overdue invoices, with its level and a business event, so that the open items register and the Storyline can show that a customer was reminded and when.

Further requirements to be written.

## Success Criteria

To be written.

## Assumptions and Dependencies

- Depends on the open items register and the overdue receivable derivation.
- Constitution III applies: a dunning record needs the scenario in this spec before any schema.

## Requirement Traceability

| Requirement | Evidence |
| --- | --- |
| FR-001 | to be filled by the plan and the tasks |
