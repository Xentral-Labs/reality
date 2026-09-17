# Feature Specification: Unified tool catalog

**Feature Branch**: `feat/unified-tool-catalog`
**Language**: English
**Created**: 2026-09-17
**Status**: Approved scope
**Input**: Present existing actions, commands, views and MCP capabilities in one understandable catalog without changing any existing MCP contract.

## Context and Intent
### Problem
Technical catalogs split the same capability across actions, commands and calculated views. Users cannot easily tell what an agent can read, explain or change.
### Scope
One searchable Tools directory, grouped by business topic and filtered by purpose, with truthful Web/MCP availability and linked technical details.
### Non-Goals
No MCP renaming, parameter/output/description changes, authorization changes, new business operations, schema, execution engine, new chat autonomy or dynamic tool selection. No automatic execution from catalog browsing.

## User Scenarios & Testing
### User Story 1 — Find a capability (P1)
A user searches or filters Tools without understanding the underlying catalogs.
Acceptance: commands and calculated-view bookmarks both open one directory; topics are visible without opening folders; search matches translated labels and technical names; filtering by topic and Read/Understand/Change works together; empty/error states are explicit.
### User Story 2 — Understand and use a capability (P1)
A user opens a capability to understand purpose, inputs and available access.
Acceptance: equivalent read representations appear once; movement forms remain distinct; existing forms and report dialogs open with company context; navigation-only shortcuts are identified; unavailable Web forms are not offered; technical details show actual MCP names and parameters without implying user/token permission.
### User Story 3 — Preserve existing integrations (P1)
An existing MCP client continues unchanged.
Acceptance: the complete registered MCP names, descriptions, schemas and access modes remain byte-equivalent; the server, handlers, proposal approval and responses are unchanged. The new catalog references existing identifiers only.

## Requirements
- **FR-001**: Replace Actions/Calculated views tabs with one Tools directory, retaining both existing URLs and company context.
- **FR-002**: Group visible capabilities by business topic; independently filter by topic and purpose (Read, Understand, Change), with translated search, counts and reset.
- **FR-003**: Deduplicate only explicit existing relationships. Preserve distinct form intents sharing a command. Every command, workspace action/view, projection and public MCP tool must remain discoverable or attached to a capability; no silently dropped entries.
- **FR-004**: Show purpose, read/change classification and actual available entrypoints. Browsing is read-only; mutations keep existing confirmation. MCP availability denotes catalog support, not the user's authorization.
- **FR-005**: Detail disclosures link actual commands, views, projections and MCP definitions and show inputs, result/effect and confirmation semantics. Existing source/code/report explanation access remains.
- **FR-006**: Preserve the complete existing MCP contract and execution path. No client migration is required.
- **FR-007**: Preserve tenant isolation, keyboard focus, responsive layout, light/dark themes and all supported UI languages. Errors do not look like an empty catalog.

## Key Entities
Capability: presentation metadata linking existing technical definitions, with stable identity, topic, purpose and supported access. Topic: a business-oriented grouping. Neither is business state.

## Assumptions and Dependencies
Approved by the user's “ok dann mach das so” after the compatibility proposal. The existing application-reference read supplies validated deployment metadata. Existing UI action eligibility remains authoritative. Technical/source descriptions keep their original wording; UI labels are localized. No unresolved clarifications.

## Success Criteria
Every existing catalog definition is represented; no duplicate read representation for explicitly linked definitions. Users reach existing forms/reports from one directory. Existing MCP clients require zero changes. Automated metadata, browser and compatibility checks pass.

## Requirement Traceability
All repository artifacts are written in English; UI translations remain localized.

| Requirement | Story | Tasks | Verification |
|---|---|---|---|
| FR-001 | US1 | T004–T007 | Legacy URL browser and section tests |
| FR-002 | US1 | T002–T007 | Filter unit/browser tests |
| FR-003 | US1 | T002–T003 | Complete catalog coverage and alias tests |
| FR-004 | US2 | T004–T007 | Eligibility, no-write and draft browser checks |
| FR-005 | US2 | T003–T007 | Technical metadata and report/form browser checks |
| FR-006 | US3 | T002–T003, T007 | MCP compatibility baseline and existing MCP tests |
| FR-007 | US1/US2 | T004–T007 | Language, mobile, error and tenant checks |
