# Research

- Decision: Share a tenant-scoped SQL inventory query in an application service. Rationale: numeric filtering and pagination must happen in PostgreSQL, without loading the full register in Web. Alternative rejected: calling an unbounded list service and slicing in Python.
- Decision: Reuse `delivery_reads.fulfillment_expressions` and `effective_value` for incoming commitments. Rationale: these already include revisions and correction-aware receipts. Alternative rejected: another hand-written commitment lifecycle rule.
- Decision: Preserve existing item/location membership and movement provenance lists. Rationale: this addresses derivation drift without broadening product scope.
- Decision: Update existing projection catalog entries, not add materializations. Rationale: stock blocks extend existing runtime calculations.
- No unresolved clarifications. No extension hooks are configured.
