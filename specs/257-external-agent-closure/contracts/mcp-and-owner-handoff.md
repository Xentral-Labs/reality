# Contract: MCP Discovery, Review Handoff and Verification

## Proposal preparation result

Every public propose action retains its current proposal ID, status, normalized arguments and
preview and adds a structured next-step description:

- current proposal identity and lifecycle;
- whether a fresh server review is required;
- canonical read or Web decision handoff for that review;
- required confirming principal and explicit-confirmation rule;
- `proposal_execution_status` as the reconciliation read after confirmation or a lost response.

The result does not assert human approval and does not manufacture or extend a state-bound token.

## Capability discovery

- Exact public MCP tool name resolves first.
- A unique registered application-tool identity may resolve to its canonical public MCP name.
- The response always states the canonical public name.
- Unknown or ambiguous identities are refused without fuzzy matching; ambiguity returns only
  bounded public candidates.

## Reservation receipt

The receipt retains proposal, commitment, reservation/event identities and exact requested,
applied and shortage quantities. It additionally states:

- `effect`: `none`, `partial` or `complete`;
- `remaining_work`: the shortage recorded by this execution;
- named reads for proposal reconciliation and current operational verification.

`effect=none` claims no Reservation or reservation-created event. It does not imply failure to
execute the command and does not imply fulfilment.

## Proposal rejection

Input is one opaque pending proposal identity plus an explicit authorized-human rejection
decision. The MCP lifecycle surface is controlled and excluded from default model-selectable
tools; an agent may invoke it only to carry out that explicit human decision. A successful result
states rejected lifecycle and attribution and creates no business effect. Safe replay of the same
rejected proposal returns stable rejected state. Executed, executing, foreign and unknown
proposals cannot be rejected.

## Invoice-credit context

Input is one opaque customer-invoice identity. Output reuses the canonical service context:
invoice/open amount, eligible position identities, credited and remaining quantities, amount
capacity and blockers. It is read-only and tenant scoped.

## Finance owner handoff

Agent credentials may prepare settlement, account, dunning, free supplier-invoice and costing
proposals. They cannot confirm owner-governed effects. An authenticated active owner reviews and
decides owner-governed settlement, account, dunning and costing proposals in Web. A free supplier
invoice follows the canonical tool policy for ordinary mutating actions: an authorized human must
explicitly confirm it, but owner-only authority is not added. MCP then reconciles the same proposal
identity and reads the resulting balances, credit, notice, invoice or cost observation.

## Public closed values

Runtime schema, capability guidance and generated Tool Usage publish the same closed values,
required fields and nested shapes. The deployed release qualification compares these properties,
not merely tool names.
