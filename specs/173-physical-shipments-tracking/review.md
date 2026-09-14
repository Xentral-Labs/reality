# Final Review: Physical Shipments and Tracking

**Review date**: 2026-09-11
**Scope**: Final working-tree diff for Spec 173
**Result**: PASS with no unresolved critical correctness or security finding

## Requirement review

| Area | Requirements | Result | Evidence |
|---|---|---|---|
| Identity, compatibility and schema | FR-001–FR-004, FR-025, DR-004, DR-010 | PASS | Tenant-scoped opaque Shipment/Package/Event/Supersession models, nullable Movement→Package link, closed constraints and tenant-first indexes in migration 0056. |
| Physical authority and returns | FR-005–FR-006, DR-002–DR-003, DR-009 | PASS | Package execution calls the existing `record_movement` service. Effective Movements remain the only stock/fulfillment authority; customer and supplier return regressions preserve original fulfillment. |
| Events, sources and corrections | FR-007–FR-011, DR-001, DR-005–DR-008 | PASS | Events are append-only, supersession is explicit, SourceRecord links remain optional/lossless, and current observations plus event history are derived at read time. |
| Reads and explanation | FR-012–FR-013, FR-029–FR-030 | PASS | Shared tenant query filters before pagination by direction, purpose, party, dates, carrier, tracking and derived observation. Detail accepts Shipment or Package identity and returns effective contents, current/history events, quantities, times, discrepancies and shortest links. Page cost is bounded at six SQL statements for 50 of 80 rows. |
| Reviewed mutations | FR-014–FR-018 | PASS | Five commands share state-bound proposal, confirmation, exact receipt, replay and reconciliation infrastructure. Preparation has no physical effect; execution remains atomic. |
| Adapter and Web parity | FR-019–FR-024, FR-028 | PASS | Web, CLI, HTTP, MCP and Chat bindings call shared services/tools. Web separates Commitments from physical Shipments and uses discovered reviewed actions. en/de/nl/es contracts and the stateful browser matrix pass. |
| Catalogs and compatibility | FR-026–FR-027 | PASS | Commands, events, tenant isolation, actions, references and projection invalidation are cataloged. Migration is additive with no historical backfill; legacy Movement and return suites pass. |

## Constitution and architecture

- Source → Evidence → Reality is preserved. Shipment and Event may link directly to immutable
  SourceRecord evidence; no synthetic Document is manufactured.
- Shipment does not store operational status, fulfillment, receipt or delivery timestamps.
  Observations, quantities and discrepancies are computed from current Events and effective
  Movements.
- Movement → ShipmentPackage → Shipment is the shortest physical-content path. No Document,
  party, tracking or Shipment fields are duplicated on Movement.
- Every business table and query is tenant-scoped. Foreign identities return not found.
- CLI, HTTP, MCP, Chat and Web contain translation only; domain eligibility and effects remain in
  shared application services.

## Rollback and operational risk

- Migration 0056 is additive. Downgrade removes only the new Shipment feature structures and the
  nullable Package link; it does not rewrite pre-existing Movement truth.
- No background job, external carrier call or secret-bearing payload logging was introduced.
- Tracking text is searchable data, never identity. External payloads remain in immutable
  SourceRecords.
- The frontend build retains the repository's existing large-chunk advisory; it is not introduced
  as a correctness or release blocker by this feature.

## Verification conclusion

No critical or high-severity finding remains. Final commands and exact results are recorded in
`quickstart.md`. The intentionally untracked `.claude/worktrees/` directory was not modified.
