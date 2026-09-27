# Data Model: Governed ERP Logic Ownership

This feature adds no persisted business entity and no database migration. These are validated
deployment-metadata concepts assembled from executable catalogs and source. They never become
tenant data, evidence, authorization or business state.

## GovernedCapability

- `identity`: stable existing command service or read-access public MCP tool identity; catalog
  self-description tools are excluded and adapter/view-only reads attach as consumers.
- `kind`: command mutation, command read or public read without a business command.
- `resource_keys` and `process_steps`: existing business classifications.
- `owner`: exactly one `AuthoritativeOwner`.
- `public_entry_points`: current CLI/Web/API/Chat/MCP/tool identities.
- `reads`, `writes`, `events`: existing data basis and effects.
- `verification_reads`, meaning boundaries and exact executable test evidence.
- optional explicit exclusion reason for a non-business transport/operational helper.

Validation: unique identity; singular mutation owner; runtime references resolve at application
startup; evidence is non-empty and its repository test node resolves in CI/docs validation;
ordering is deterministic; no unexplained public business entry is absent. Production runtime does
not require repository test files.

## AuthoritativeOwner

- current primary command `service` or capability-guidance `application_tool`;
- resolved source path and function;
- exact semantic question/effect owned;
- supporting services that do not acquire ownership;
- optional critical-calculation family and grain.

Validation: one callable resolves, dependencies point inward, a mutating application tool maps to
one command owner or explicit exclusion, and supporting services do not register a second owner.

## CapabilityTrace

Generated immutable presentation joining a governed capability to owner, classification,
consumers, effects and evidence. Catalog construction and generated docs consume it. Business
calculations and mutation authorization never do.

## BoundaryException

- exact architecture rule, repository path and function;
- rationale for the temporary/necessary boundary;
- executable evidence that no competing authority/effect exists.

Every field resolves; one exception matches exactly one current finding; unused, stale or broadened
exceptions fail. It has no runtime lifecycle.

## CriticalCalculationOwner

- approved family, semantic question and grain;
- one authoritative owner and registered consumers;
- shared scenario evidence and applicable known/unknown/stale/refused states.

Every consumer must be covered; new consumers fail until covered; disagreement blocks
consolidation.

| Family | Named question | Important distinction |
|---|---|---|
| Inventory | Exact positions; operational item/location register | Aggregation parity, not one universal grain |
| Fulfilment | Effective, qualifying fulfilled and clamped open quantity | Reservation/hold context is not movement |
| Finance | Invoice settlement position; party/currency total with credit | Invoice open, credit, party net and account balance remain distinct |
| Contribution | Canonical DB arithmetic; candidate/reviewed evidence state | Candidate, reviewed, stale and unknown never collapse |
