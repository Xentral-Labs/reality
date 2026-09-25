# Feature Specification: MCP Permission Ceiling Follows the Catalog

**Feature Branch**: `269-mcp-permission-ceiling`
**Language**: English
**Created**: 2026-09-25
**Status**: Draft
**Input**: The interactive consent flow refuses more than 200 tool permissions while the catalog holds 180. Make the accepted length a consequence of the catalog instead of a literal that expires without warning.

## Context and Intent

### Problem

Interactive MCP authorization preselects every tool the requested scopes make eligible, and the
approval endpoint accepts at most 200 tool names. The catalog holds 180 tools. Twenty additions
from now the default selection is refused by input validation before any business rule runs: the
consent page shows `Reality API returned 422`, because the validation error's body is a list the
browser cannot read as a sentence; the interaction expires ten minutes later, and no external
client can complete a connection at all. Nothing fails earlier, because no test compares the
accepted length with the catalog it is meant to bound.

A second refusal on the same endpoint is worse. An unknown tool name raises from the shared
validation as a `ValueError`, which the handler does not catch, so it reaches the owner as a server
error. The manual token path answers the same input with a stated sentence.

The two paths that grant the same permissions also disagree. Manual company tokens accept any list
the shared permission validation accepts, with no length bound; interactive grants are capped at
200. One path will start refusing what the other still accepts, for the same catalog.

The bound itself is also applied too early to be true. Input validation counts the raw submitted
list, while the shared validation afterwards collapses duplicates and resolves legacy names. A
submission that is legitimate once normalized can be refused before normalization runs.

### Scope

Derive the accepted permission-list length from the catalog, apply it after the list is normalized,
apply the same rule to both grant paths, and state the reason when a list is refused so the consent
screen can show it. Pin the relationship with a test that reads the catalog rather than a number.

### Non-Goals

- Do not change which tools a scope makes eligible, or any tool's access class.
- Do not introduce wildcard permissions for interactive OAuth grants. A grant keeps naming its
  tools; this feature only removes an arbitrary ceiling on how many it may name.
- Do not extend an already issued token or grant to tools added after it was issued. An allowlist
  is a frozen list of names, so every credential issued before a catalog addition permanently lacks
  that addition, and an agent meets it as a refused call rather than as a missing tool. That is a
  real and separate gap; it is recorded here and decided elsewhere.
- Do not redesign the consent screen's layout, its presets, or its zero-permission default.

## User Scenarios & Testing

### User Story 1 - Connecting an external agent survives catalog growth (Priority: P1)

As the owner of a company, I can complete the browser consent for an external MCP client with every
eligible tool selected, and that stays true as Reality gains capabilities.

**Why this priority**: Without it, a future merge that adds the twenty-second tool silently disables
every new external connection, and the cause is invisible from the failure.

**Independent Test**: Submit an approval that names every tool the requested scopes make eligible
and verify it is accepted, with the expected count taken from the catalog at test time rather than
written into the test.

**Acceptance Scenarios**:

1. **Given** a pending authorization requesting all supported scopes, **When** the owner approves
   with the complete preselected list, **Then** the grant is created and names every selected tool.
2. **Given** the catalog grows by one tool, **When** the same approval is submitted, **Then** it is
   still accepted and no length limit needs editing.
3. **Given** a submitted list that repeats a tool name, **When** it is approved, **Then** the list
   is normalized first and the grant holds each tool once.

---

### User Story 2 - A refused permission list says what is wrong (Priority: P2)

As the owner, when an authorization is refused I am told which part of the request was rejected,
instead of a generic failure on a page whose interaction is about to expire.

**Why this priority**: The current failures read as a status code or a server fault, which is
indistinguishable from a network error, an expired interaction, or a revoked client, so neither can
be acted on.

**Independent Test**: Submit a permission list containing an unknown name and a list longer than the
catalog, and verify each response names its cause and that the consent screen renders that text.

**Acceptance Scenarios**:

1. **Given** a permission list naming a tool that does not exist, **When** it is approved, **Then**
   the refusal names the unknown tool and no grant is created.
2. **Given** a permission list longer than the catalog after normalization, **When** it is approved,
   **Then** the refusal states that more permissions were requested than exist.
3. **Given** any refused approval, **When** the consent screen handles it, **Then** it shows the
   stated reason rather than a bare status code or a server error, and the authorization remains
   pending until it expires on its own.

---

### User Story 3 - Both grant paths accept the same permissions (Priority: P3)

As the owner, a permission set I can put on a manual company token is one I can also approve for an
interactive client, and the other way round.

**Why this priority**: The divergence has no product meaning; it exists because one endpoint carries
a literal the other does not.

**Independent Test**: Submit the same complete permission list through manual token creation and
through interactive approval and verify both are accepted, and that both refuse the same
over-long or unknown list with the same stated reason.

**Acceptance Scenarios**:

1. **Given** the complete catalog as a permission list, **When** it is submitted to manual token
   creation and to interactive approval, **Then** both accept it.
2. **Given** a list longer than the catalog, **When** it is submitted to either path, **Then** both
   refuse it with the same reason.

---

### Edge Cases

- A wildcard permission remains one entry and is never measured against the catalog length.
- Legacy tool names resolve to their current names before the list is measured, so a rename cannot
  make a valid list appear too long.
- An empty list stays refused by the existing rule that at least one permission is required.
- A list at exactly the catalog length is accepted; one name beyond it cannot be legitimate, because
  every name is already required to exist and duplicates are already collapsed.
- A client that requests only one scope still receives a working consent, with only that access
  class eligible.

## Requirements

### Functional Requirements

- **FR-001**: The accepted number of named tool permissions MUST be derived from the current tool
  catalog and MUST NOT be a separately maintained number.
- **FR-002**: The length of a permission list MUST be measured after the list is normalized, that
  is after duplicates are collapsed and legacy names resolved.
- **FR-003**: Interactive approval and manual token creation MUST apply the same permission
  validation, including the same bound and the same refusal reasons.
- **FR-004**: A refused permission list MUST state its cause: an unknown tool name, more
  permissions than the catalog holds, or an empty selection.
- **FR-005**: The consent screen MUST present a refusal's stated reason, and a refused approval MUST
  leave the authorization pending rather than consuming it.
- **FR-006**: Approving with every eligible tool selected MUST succeed for every combination of
  supported scopes.
- **FR-007**: An automated check MUST fail when the catalog grows beyond what the grant paths
  accept, so the condition is discovered in CI rather than in a connection attempt.

### Key Entities

- **Tool permission list**: the explicit tool names a credential may call, stored per manual token
  and per interactive grant, validated identically for both.
- **Tool catalog**: the authoritative set of MCP tool names, which is also the only legitimate
  bound on a permission list's length.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An owner can approve an interactive authorization with all 180 currently eligible
  tools selected, and the proof reads that number from the catalog rather than stating it.
- **SC-002**: Adding a tool to the catalog requires no edit to any permission-length limit, in any
  layer, for either grant path.
- **SC-003**: Every refusal of a permission list names its cause, and the consent screen shows that
  text.
- **SC-004**: Manual token creation and interactive approval accept and refuse the same permission
  lists in an executed comparison.

## Assumptions and Dependencies

- The shared permission validation stays the single place that resolves legacy names, collapses
  duplicates and rejects unknown tools.
- Access classes and the scope each one requires remain authoritative from the existing catalog.
- Zero permissions by default, explicit review of change-capable permissions, and human
  confirmation remain unchanged; this feature touches only how many named permissions are accepted.
- The consent interaction's existing ten-minute lifetime is unchanged.

## Requirement Traceability

FR-001, FR-002 and FR-006 → US1. FR-004 and FR-005 → US2. FR-003 → US3. FR-007 → US1 as its
standing regression proof, and SC-002 as its measurable form.
