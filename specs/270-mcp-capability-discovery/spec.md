# Feature Specification: One Way In to the Capability Catalog

**Feature Branch**: `270-mcp-capability-discovery`
**Language**: English
**Created**: 2026-09-25
**Status**: Approved
**Input**: A connected agent has no way to ask what Reality can do, and reads a permission refusal as a missing capability. The classification that answers both already exists and never leaves the process.

## Context and Intent

### Problem

An agent connected over MCP receives two sentences of server instructions and 179 flat tools. It has
no way to ask what business areas exist, no way to tell a capability it may not use from one that
does not exist, and no way to recognise a capability under the name its user gives it. Three
consequences, all observed:

1. **A refusal reads as an absence.** The tool listing is not filtered per credential, so every
   agent sees all 179 tools whatever its grant allows. A call outside the grant fails with
   `MCP token does not allow tool: <name>`. An agent reports that as the capability being
   unavailable. A test run reported the dunning capability missing in exactly this way, although
   `finance_dunning_context`, `finance_dunning_notices`, `finance_dunning_notice`,
   `finance_dunning_record_propose` and `finance_dunning_reverse_propose` have been deployed since
   2026-09-24.
2. **There is no entry point.** A client that searches or defers tools instead of loading all 179
   cannot discover a field it does not already name. `capability_describe` requires the tool name
   being looked for, which is the thing that is missing, and `business_records_discover` answers
   about records rather than capabilities.
3. **Only English carries meaning.** Every tool name, label, description and schema over MCP is
   English by repository rule. "Mahnwesen" appears nowhere in the surface, so a German question
   matches nothing by text, although the repository already holds `Mahnung erfassen` and
   `Mahnung stornieren` as the German labels for those same capabilities.

The classification that answers all three is already built and never crosses the boundary.
`reality.tool_catalog` gives each of the 179 tools a topic from the eleven in
`config/tool_catalog.json` — Orders and commitments, Invoices and payments, Stock and warehouse,
Issues and approvals, and so on — together with a purpose of read, understand or change, a business
description, the commands and views it shares a capability with, and, for 99 of the 167 capability
entries that carry MCP tools, a German label. That structure feeds the generated documentation and
the command palette. Over MCP it is invisible, and the `group` the tool definitions carry is not
transmitted either.

### Scope

Expose the existing capability classification through one read tool, in two steps so that the first
answer stays small: the topics, then the capabilities of one topic with their tools. Mark each
listed tool with whether the calling credential may call it and, when it may not, why. Name that
tool in the server instructions as the way in.

### Non-Goals

- Do not filter the tool listing per credential. A tool absent from the listing is indistinguishable
  from a tool that does not exist, which is the confusion this feature removes rather than a cure
  for it; the listing stays complete and the discovery answer carries the grant state.
- Do not invent a second topic vocabulary, and do not reclassify existing tools.
- Do not change any tool's access class, what a scope makes eligible, or what a grant allows.
- Do not translate tool names, descriptions or argument schemas. Only the business label of a
  capability carries another language.
- Do not add a change capability, a confirmation step, or any write.
- Do not expose tenant business data. This answers what can be done, not what is the case.

## User Scenarios & Testing

### User Story 1 - An agent can ask what this company can do (Priority: P1)

As an external agent connected to a company, I can ask which business areas Reality covers and then
which capabilities one area holds, so I can answer a question about a field I was not told the name
of.

**Why this priority**: Without an entry point, every other improvement depends on the client having
loaded all 179 tools, which the clients in use do not guarantee.

**Independent Test**: Call the discovery tool with no arguments and confirm it returns the eleven
topics; call it for one topic and confirm it returns that topic's capabilities with their tools,
purposes and descriptions.

**Acceptance Scenarios**:

1. **Given** a connected agent, **When** it calls the discovery tool without arguments, **Then** it
   receives every topic with its label and how many capabilities it holds.
2. **Given** a topic, **When** the agent asks for it, **Then** it receives that topic's
   capabilities, each with its business label, description, purpose and the MCP tools bound to it.
3. **Given** the complete set of topics, **When** every topic is collected, **Then** each of the
   179 catalog tools appears at least once.
4. **Given** an agent that knows only the discovery tool, **When** it looks for dunning, **Then**
   two calls reach the five dunning tools under Invoices and payments.

---

### User Story 2 - An agent can tell "not granted" from "does not exist" (Priority: P1)

As an external agent, I can see that a capability exists and that my credential was not given it, so
I report a permission to widen rather than a capability that is missing.

**Why this priority**: This is the failure that was actually observed, and it misinforms the person
asking: they are told to build something that is already built.

**Independent Test**: Connect with a credential granted a strict subset of the catalog and confirm
the discovery answer marks the granted tools usable and the others not, each with its reason.

**Acceptance Scenarios**:

1. **Given** a credential whose grant omits a tool that exists, **When** the agent discovers that
   tool's topic, **Then** the tool is listed, marked not callable, with the reason that the grant
   does not include it.
2. **Given** a credential whose scopes exclude an access class, **When** the agent discovers a topic
   containing a tool of that class, **Then** the tool is listed, marked not callable, with the
   reason that the credential's scopes exclude its access class.
3. **Given** a credential granted every tool, **When** it discovers any topic, **Then** every tool
   there is marked callable.
4. **Given** a tool marked callable, **When** the agent calls it, **Then** it is not refused for
   permission reasons.

---

### User Story 3 - A capability is findable under its business name (Priority: P3)

As a person working in German, I can ask for "Mahnwesen" and the agent reaches the dunning
capabilities, because the discovery answer carries the business label alongside the English one.

**Why this priority**: It removes a whole class of false "not supported" answers, but only after the
entry point and the grant state exist; without those it has nothing to attach to.

**Independent Test**: Read the discovery answer for Invoices and payments and confirm the recording
and reversal capabilities carry their German labels next to the English ones.

**Acceptance Scenarios**:

1. **Given** a capability that has a German label in the resource catalog, **When** it is
   discovered, **Then** the answer carries that label beside the English one.
2. **Given** a capability that has no German label, **When** it is discovered, **Then** the English
   label is given and the answer does not present the gap as an error.

---

### Edge Cases

- A credential with a narrow grant still receives the complete catalog with each entry marked,
  because hiding what is not granted reproduces the confusion the feature exists to remove.
- A tool bound to more than one capability entry — eleven are today — is listed under each, with the
  same grant state in each, and is counted once for coverage.
- An unknown topic is refused by naming the topics that exist.
- The discovery tool lists itself, as a read capability every credential holding it can call.
- The answer describes capabilities only; it never reveals whether the company holds any records of
  the kind a capability acts on.

## Requirements

### Functional Requirements

- **FR-001**: A read tool MUST return, without arguments, every capability topic with its label and
  the number of capabilities it holds.
- **FR-002**: The same tool MUST return, for one named topic, that topic's capabilities with their
  business label, description, purpose and the MCP tools bound to each.
- **FR-003**: Every tool in the MCP catalog MUST appear under at least one topic, and the topics
  MUST be the existing eleven; the tool MUST NOT introduce a second vocabulary.
- **FR-004**: Each listed tool MUST state whether the calling credential may call it, and when it
  may not, whether the grant omits it or the credential's scopes exclude its access class.
- **FR-005**: A capability MUST carry its German business label where the catalog holds one, and
  fall back to the English label where it does not.
- **FR-006**: The server instructions MUST name this tool as the entry point for discovering
  capabilities.
- **FR-007**: The tool MUST be classified as read: no confirmation, no side effects, no tenant
  business data in its answer.
- **FR-008**: A tool added to the MCP catalog MUST appear in discovery without editing the
  discovery tool.

### Key Entities

- **Capability topic**: one of the eleven existing business areas, with a label, that every MCP tool
  is already assigned to.
- **Capability**: a unit of business meaning that binds a label, a description, a purpose and the
  MCP tools, commands and views that realise it.
- **Grant state**: per tool and per calling credential, whether it may be called and, when not,
  which of the two reasons applies.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An agent holding only the discovery tool reaches any of the eleven business areas in
  at most two calls.
- **SC-002**: For a credential that lacks a tool, the answer states that the tool exists and is not
  granted, and that state is distinguishable from a name that does not exist.
- **SC-003**: Every one of the 179 catalog tools appears at least once across the topics, proven
  against the catalog rather than a written list.
- **SC-004**: Every capability holding an MCP tool that has a German label in the resource catalog
  carries it in the answer; the rest carry the English label.
- **SC-005**: Adding an MCP tool changes no discovery code, and the coverage proof fails if the new
  tool is unclassified.

## Assumptions and Dependencies

- The eleven topics of `config/tool_catalog.json` and the classification built from them remain
  authoritative; this feature transmits them and does not restate them.
- The tool listing stays complete for every credential, per the non-goal above.
- The server-verified principal already carries the calling credential's allowed tools and scopes,
  so the grant state needs no new authority.
- The existing gates for a new tool apply: a capability topic, a read block in the command catalog
  declaring no confirmation and no side effects, the tenant isolation catalog, the reporting-graph
  and coverage-matrix checks, and regenerated Tool Usage documentation. They belong in the plan.
- German labels exist for 99 of the 167 capability entries that carry MCP tools today; completing
  them is the resource catalog's own concern and not a condition of this feature.

## Requirement Traceability

FR-001, FR-002, FR-003 and FR-008 → US1. FR-004 → US2. FR-005 → US3. FR-006 → US1 as the way an
agent learns the entry point exists. FR-007 → all three stories as the boundary they stay inside;
SC-003 and SC-005 are the executed form of FR-003 and FR-008.
