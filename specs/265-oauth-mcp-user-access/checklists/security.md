# Security Requirements Checklist: OAuth MCP User Access

**Purpose**: Validate authorization, tenancy, consent, recovery and interoperability
requirements quality before implementation
**Created**: 2026-09-24
**Feature**: [spec.md](../spec.md)

**Ownership**: This is a reviewer-owned requirements-quality artifact. `[x]` means a
reviewer found the written requirement sufficient; it does not mean implementation is
complete. Implementation agents read but do not change these markers.

## Requirement Completeness

- [ ] CHK001 Are requirements defined for every authorization boundary: MCP resource,
  authorization issuer, browser session, grant, credential, company membership, tool
  scope and business confirmation? [Completeness, Spec §FR-001–FR-012]
- [ ] CHK002 Are both interactive-user grants and retained unattended-integration
  credentials explicitly covered without conflating their owners or lifecycle?
  [Completeness, Spec §FR-017–FR-018]
- [ ] CHK003 Are company creation, initialization, recovery and final grant eligibility
  all specified as separate states and decisions? [Completeness, Spec §FR-013–FR-014]
- [ ] CHK004 Are grant inspection and revocation requirements defined for both the
  authorizing user and the company owner? [Completeness, Spec §US4, FR-015]
- [ ] CHK005 Are protocol discovery, authorization, token renewal, revocation and
  insufficient-authority requirements all represented in the external contract?
  [Completeness, Contract §oauth.md]
- [ ] CHK006 Are account/security schema additions justified by repeated authorization
  decisions while business-schema expansion remains explicitly excluded? [Completeness,
  Plan §Data and migration impact, Data Model §Design boundary]

## Requirement Clarity

- [ ] CHK007 Is “one company per grant” unambiguous across initial authorization,
  re-consent and company switching? [Clarity, Spec §FR-005, FR-016]
- [ ] CHK008 Are the meanings and intersection rules for OAuth scopes, exact tool
  allowlists, current membership roles and operation-specific policies clearly
  distinguished? [Clarity, Spec §FR-007–FR-009]
- [ ] CHK009 Is the exact boundary between OAuth consent, company-creation confirmation,
  proposal creation and proposal execution confirmation stated consistently?
  [Clarity, Spec §FR-012–FR-014]
- [ ] CHK010 Are “short-lived”, “bounded” and renewal periods quantified wherever they
  affect acceptance or security review? [Clarity, Plan §Failure, Data Model
  §MCPAuthorizationInteraction/§MCPUserCredential]
- [ ] CHK011 Are the client identity and redirect validation requirements specific for
  both pre-registered clients and CIMD clients? [Clarity, Contract §Client metadata
  validation]
- [ ] CHK012 Is the supported-client baseline explicit enough to determine whether a
  client is conforming, unsupported or needs a separately reviewed compatibility path?
  [Clarity, Spec §FR-021–FR-022, Research §Client registration compatibility]

## Requirement Consistency

- [ ] CHK013 Do the spec, plan and contracts consistently keep the MCP runtime a
  stateless resource server and the API/account runtime the authorization issuer?
  [Consistency, Plan §Summary, Research §MCP protocol]
- [ ] CHK014 Do all artifacts consistently permit ready Sandboxes through both MCP
  credential kinds while preserving identical tenant, tool, proposal and explicit-
  confirmation controls and canonical company-setup behavior?
  [Consistency, Spec §FR-013–FR-014, Plan §Failure, Research §Company creation]
- [ ] CHK015 Do grant revocation, membership removal, account disablement and company
  archival requirements agree that live effective authority ends on the next request?
  [Consistency, Spec §FR-007, FR-015, SC-004]
- [ ] CHK016 Are manual MCP tokens explicitly unchanged in data model, management,
  dispatch and rollout requirements? [Consistency, Spec §FR-017–FR-018, Plan §Rollout]
- [ ] CHK017 Do actor-attribution requirements remain consistent with the prohibition on
  client-supplied tenant/user authority? [Consistency, Spec §FR-018–FR-019, DR-003]
- [ ] CHK018 Are retention, audit and secret-redaction requirements consistent between
  data-model lifecycle fields and observable management views? [Consistency, Spec
  §FR-019, Data Model §Migration and retention]

## Acceptance Criteria Quality

- [ ] CHK019 Can every denial class in SC-002 be objectively distinguished and proven
  before application-tool dispatch? [Measurability, Spec §SC-002]
- [ ] CHK020 Does SC-004 define an observable timing boundary for effective revocation
  rather than relying on eventual cleanup? [Measurability, Spec §SC-004]
- [ ] CHK021 Are duplicate-prevention outcomes measurable independently for company,
  membership, setup run, grant and business effect? [Measurability, Spec §SC-005]
- [ ] CHK022 Is the two-client interoperability criterion bounded by named protocol
  capabilities rather than client-specific manual accommodations? [Measurability, Spec
  §SC-008, Plan §Rollout]
- [ ] CHK023 Is “no usable credential material” defined across storage, management
  responses, URLs, logs, browser persistence and audit detail? [Measurability, Spec
  §SC-009, Contract §Browser Interaction]

## Scenario and Edge-Case Coverage

- [ ] CHK024 Are primary, alternate, denial, expiry, replay, outage, recovery and
  revocation scenarios specified for the authorization lifecycle? [Coverage, Spec §US1,
  US4, US5, Edge Cases]
- [ ] CHK025 Are concurrent approval, code exchange, refresh, membership removal and
  revocation races covered by atomic outcome requirements? [Coverage, Plan §Failure]
- [ ] CHK026 Are same-name companies, account switching during consent and stale Web
  sessions addressed without relying on display values as identity? [Coverage, Spec
  §Edge Cases]
- [ ] CHK027 Are client metadata fetch redirects, DNS rebinding, private/reserved
  destinations, response size and timeout boundaries specified? [Coverage, Contract
  §Client metadata validation]
- [ ] CHK028 Are scope elevation, exact-tool catalog growth and tool removal scenarios
  defined without silently broadening an existing grant? [Coverage, Spec §FR-008–FR-009]
- [ ] CHK029 Are lost company-setup responses and not-ready/failed setup outcomes
  specified so consent cannot bind an unusable company? [Coverage, Spec §US3]
- [ ] CHK030 Are rollback requirements defined for enabled interactive grants when the
  previous MCP release cannot understand them? [Recovery, Plan §Rollout and Rollback]

## Domain and Dependency Boundaries

- [ ] CHK031 Is it explicit that authorization records never become business Evidence,
  Reality, document status or proposal/execution receipts? [Domain Consistency, Spec
  §DR-001–DR-005]
- [ ] CHK032 Are the shortest access relationships documented without duplicating
  Document, SourceRecord or operational-record links? [Domain Consistency, Data Model
  §Design boundary]
- [ ] CHK033 Are current MCP SDK compatibility and the selected `2026-07-28` protocol
  behavior identified as a proven dependency rather than an assumption hidden in
  implementation? [Dependency, Plan §Review Risks]
- [ ] CHK034 Is the non-goal of Dynamic Client Registration consistent with the two-client
  success criterion and documented fallback policy? [Dependency, Spec §FR-022,
  Research §Client registration compatibility]
- [ ] CHK035 Are documentation generation obligations clear if principal/tool schema or
  catalog metadata changes, without implying an unreviewed catalog change is required?
  [Dependency, Plan §Test Strategy]

## Review

- **Specification reviewer**: Owner approval recorded in conversation, 2026-09-24
- **Domain/architecture reviewer**: Owner approval recorded in conversation, 2026-09-24
- **Security requirements reviewer**: _Pending_
- **Decision**: Pending reviewer completion

## Notes

- Reviewers should record findings beside the relevant item and update the source
  artifact before marking an item complete.
- `$speckit-implement` reads checklist state but does not modify reviewer markers.
