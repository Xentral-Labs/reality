# Implementation Plan

## Technical Context
Python/Pydantic2/SQLAlchemy2; no schema migration or new dependency. Domain contract
then canonical service, narrow read tool, executable catalogues and generated docs.

## Constitution Check
PASS: original source/input immutable; no accepted Reality or source-value
recalculation; tenant-scoped shared reads; no schema or infrastructure expansion;
explicit human decisions remain future work; tests and independent review required.
No exceptions.

## Smallest Implementation
- `domain/shopify_intake_preflight.py`: strict input/report contracts and semantic digest.
- `services/shopify_intake_preflight.py`: exact original source/job/stream read,
  canonical verified-buyer reader, current company/location and unique active SKU
  observations, canonical GraphQL support/projection, bounded diagnosis only.
- `tools/shopify_intake_preflight.py` plus normal application/MCP read registration.
- Existing command/resource/tenant catalogues, translations only if needed, generated docs.

No call to prepare_intake/prepare_order, no ephemeral fabricated ImportJob or
mapping overrides, no process_import_job and no ORM persistence. A no_autoflush
read boundary prevents unrelated pending ORM state from being written implicitly.
Acquisition gaps or stale requested basis refuse instead of returning fresh data.
Unsupported selected entity returns a named support blocker and no interpreted
line/item claims. Reports beyond the serialized bound refuse.

## Current Gaps Kept Visible
Existing prepare_order chooses first SKU and supplies item.unit or pcs; this read
must diagnose unique active identity and unknown source unit instead. GraphQL
projection does not supply stated line totals/delivery/unit evidence; do not infer
upstream absence. Credit assessment currently belongs to prospective preparation;
this packet does not duplicate those rules or claim financial execution readiness.

## Verification and Rollback
Test first on an owned disposable PostgreSQL schema. Capture exact source/job and
all persistent row counts before/after, plus SQL statements to exclude writes.
Exercise stale/foreign pins, mapping state, company role/location, SKU cardinality,
quantity/unit/completeness, limits/digest and MCP permission. Run applicable
catalogue/spec/lint/doc gates and independent review. Remove/read-token permission
or stop advertising this optional capability to roll back; no persistent state to
undo. Schema99 deployment remains a separate reviewed proof if later requested.
