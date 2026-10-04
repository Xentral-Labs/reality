# Feature Specification: The Capability Catalog Names the Company's Purpose

**Feature Branch**: `362-tenant-purpose-in-capability-catalog`

**Created**: 2026-10-04

**Status**: Accepted

**Language**: English

**Input**: A client connected over MCP cannot tell a sandbox company from a business company.
On a sandbox company proposals preview flat, with no review token; on a business company they
carry one. Today the client asks a person to declare which it is talking to.

## Context and Intent

### Problem

Tenant purpose (`business` or `playground`) is fixed at creation and changes how proposals
behave, yet no MCP read exposes it. `capability_catalog` is the read every client is told to
call first (spec 270).

### Scope

- The topic index of `capability_catalog` carries `tenant.purpose` for the credential's own
  company.

### Non-Goals

- Nothing else about the company is exposed: no id, name, plan or settings.
- No new tool, schema or input. No `environment` field; Reality holds none.
- Single-topic answers are unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Know the company's purpose before proposing (Priority: P1)

1. **Given** a business company, **When** a client reads `capability_catalog`, **Then** the
   answer carries `tenant: {purpose: "business"}`.
2. **Given** a sandbox company, **Then** it carries `tenant: {purpose: "playground"}`.
3. **Given** a token of one company, **Then** it reads that company's purpose only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The topic index MUST carry `tenant.purpose`, read from the stored company
  record of the calling tenant.
- **FR-002**: The `tenant` object MUST contain no other key.

### Domain and Architecture Requirements

- **DR-001**: The value is recorded by the company, never derived (AGENTS rule 11), and the
  read is tenant-scoped like every other.

## Success Criteria *(mandatory)*

- **SC-001**: A client knows whether proposals preview flat without asking a person.

## Assumptions and Dependencies

- Builds on spec 270. Additive key only; existing readers are unaffected.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US1.1, US1.2, US1.3 | `packages/reality-core/tests/test_capability_catalog.py::test_topic_index_names_the_tenant_purpose`, `::test_the_token_reads_only_its_own_tenant_purpose` |
| FR-002 | US1.3 | `packages/reality-core/tests/test_capability_catalog.py::test_the_token_reads_only_its_own_tenant_purpose` |
| DR-001 | US1 | `packages/reality-core/src/reality/services/capability_catalog.py::_tenant` |
| SC-001 | US1 | `packages/reality-core/tests/test_capability_catalog.py::test_topic_index_names_the_tenant_purpose` |
