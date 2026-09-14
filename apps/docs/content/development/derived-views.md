# Develop Metrics and Operational Warnings

First inspect the generated [Projection](../tool-usage/views) and
[Exception](../tool-usage/exceptions) catalogs to avoid creating a second answer to the same
question.

## Add a Projection

Use a Projection when several consumers repeatedly need the same derived answer, such as physical,
reserved and available inventory. Define the question first, then the authoritative Reality records
and formula that answer it. A Projection is rebuildable and never becomes another source of truth.

Register its producer, consumers and invalidating Business Events. Keep tenant scope in every query,
define deterministic ordering and pagination for registers, and provide an explanation path back to
the underlying records.

### Code example: inventory position

Follow `inventory_position` in `packages/reality-core/src/reality/services/projections.py`:

- `OPERATIONAL_PROJECTIONS` declares the supported name.
- `_build_operational_rows` calls tenant-scoped `inventory_rows` and emits one stable `record_key`
  per item with physical, reserved, available, incoming and projected quantities.
- `refresh_operational_projections` rebuilds stale rows; `projection_rows` is the shared,
  deterministically ordered read entry point.
- `config/projection_catalog.yaml` documents records, calculation, outputs and consumers.

Implement the row builder, include it in `_build_operational_rows`, and add its name and catalog
entry. Add event invalidation when the global sequence is insufficient. Copy tenant, rebuild and
stale-check cases from `test_materialized_projections.py`; extend the catalog and HTTP tests when
those surfaces expose it.

## Add an Exception derivation

Use an Exception when a deterministic current condition requires operational attention. Define:

- the exact condition and when it clears;
- severity and stable class identity;
- the affected Reality record and shortest trace;
- the operational role that should investigate; and
- executable evidence for derivation, tenant isolation and clearing.

Register the class and derivator in the operational Exception catalog. Do not create a manually
closed ticket or copy status onto a Document. If resolving the condition needs a mutation, use a
normal Command and its approval boundary.

### Code example: commitment at risk

`packages/reality-core/src/reality/services/exceptions.py` contains `_outgoing_commitment_at_risk`
and registers it in `DERIVATION_REGISTRY`. Its entry in `config/operational_exception_catalog.yaml`
defines stable class ID, label, severity, affected record type, authority and evidence. When the
condition disappears, the derived Exception disappears too.

Add catalog entry and derivator together. Test appearance and clearing, tenant isolation, stable
cause IDs and the explanation trace. Use `operational_exceptions/test_derivation.py`,
`test_coverage.py` and `test_explanation.py` as templates.
