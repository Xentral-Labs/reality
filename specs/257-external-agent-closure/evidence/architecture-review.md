# Architecture Review

**Date**: 2026-09-23
**Conclusion**: The local implementation preserves the Constitution boundaries. Final release
approval remains contingent on the fresh deployed qualification and final Spec Kit analysis.

## Source → Evidence → Reality

- Free supplier invoices retain one immutable SourceRecord, stated Document and DocumentLines,
  then post the payable. They do not invent a purchase commitment or Movement.
- Invoice-linked credits retain their own source and credit DocumentLines. Each credited line uses
  the direct `billed_document_line_id` link to the exact invoice line; physical return disposition
  remains a separate Movement decision.
- Return dispositions retain a source-backed resolving Movement and preserve the arrived return's
  applicable commitment, location, lot, serial, and handling-unit identity.
- Cost reads derive guidance from retained cost bases and reviews. They create no source, event,
  projection, or business row and do not substitute zero or an inferred price for missing evidence.

Executable evidence: `test_external_agent_audit_closure.py`, the complete backend suite, and the
focused finance, return, costing, provenance, and operational-exception runs recorded in
`verification.md`.

## Shortest links and opaque identity

- Reservation remains linked to Commitment rather than duplicating source or document identity.
- Credit positions link directly to invoice positions, which retain the existing underlying order
  evidence link.
- Return resolution follows the arrived return Movement and its delivery Commitment.
- Public workflows use opaque IDs for joins and reconciliation. Human document numbers remain
  display or source-stated values, never identity.

No schema expansion was introduced for Spec 257. Existing SourceRecord, Document/DocumentLine,
Movement, LedgerEntry, ChangeProposal, and cost-authority records carry the required evidence.

## Shared services and adapter parity

- Web, MCP, Chat, and CLI contracts route through the shared application tools/services.
- Proposal preparation is effect-free. Company credentials and tenant members may prepare
  supported costing work without acquiring owner authority.
- Confirmation independently reauthorizes the authenticated active owner for governed costing,
  settlement, credit, and dunning decisions.
- Proposal rejection is a controlled human lifecycle action, excluded from default model tool
  selection, tenant-scoped, replay-safe, and without business effect.
- Independent reads reconcile effects after confirmation; mutation receipts are not treated as the
  sole proof of retained state.

## Tenant isolation and closed vocabularies

- Repository and service reads remain tenant-scoped; foreign identities return no business data.
- Manual document creation exposes exactly six operational types. Unknown upstream labels remain
  lossless payload evidence and do not become an operational type automatically.
- Movement types and payment directions are validated before durable proposal or business-record
  creation. Invalid probes leave proposal and business-record counts unchanged.
- Generated schema contracts derive the same enums as runtime validation. Deployed parity still
  requires the T074 capture.

## Review outcome

The local implementation satisfies DR-001 through DR-008 with automated evidence: source/evidence
lineage, shortest relationships, no recomputation, shared-service parity, tenant isolation,
separate owner authority, and no schema migration. This review does not substitute for T075's
fresh external public-surface run or T081's final cross-artifact analysis.

## Compatibility, rollout, and rollback

- No migration or stored-field change is present; rollback is application-code and generated-doc
  rollback only.
- Existing legacy customer-credit input remains supported as a distinct shape. New invoice-linked
  credit, free supplier invoice, dunning, rejection, and cost-guidance surfaces are additive.
- The intentionally stricter document, movement, and payment vocabularies fail before persistence;
  lossless source intake remains unchanged.
- Generated Tool Usage documentation is committed with the runtime catalogs and passed the
  post-commit catalog check.
- `docs/V0_CHECKLIST.md` was not changed because the fresh deployed CanisPro qualification and
  final F1–F13 closure matrix remain open release evidence rather than completed V0 proof.
