# Tenant Isolation Catalog Contract

## Purpose

The catalog is the executable map between the public business surface and tenant-
isolation evidence. It is evidence metadata only and grants no runtime authority.

## Required Structure

- `version`: positive schema version.
- `discovery.modules`: explicit modules whose top-level public operations are discovered.
- `families`: ordered unique isolation families.
- `explicit_operations`: public or indirect-context operations not safely found by
  signature discovery.

Each family requires a stable `key`, description, approved classification, non-empty
operation list, governing authority, and named evidence. `global_admin` entries and
reviewed exclusions also require a narrow reason.

## Discovery and Validation

The validator MUST:

1. discover public tenant-aware operations in configured modules;
2. include explicit indirect-context operations;
3. include every registered projection and application tool;
4. include services referenced by canonical command/projection catalogs;
5. reject uncovered, stale, or duplicate mappings;
6. reject unknown classes, missing authority/evidence, and broad exemptions;
7. reject evidence mappings that do not explicitly cover every operation assigned to
   the family and its classification-specific isolation behavior;
8. report failures in deterministic family/operation order.

Private helpers, fixtures, migrations, and transports are outside callable discovery. A
public-looking exclusion requires a catalog reason.

## Evidence Semantics

- `record_read`: foreign and unknown IDs yield equivalent non-disclosing `NotFound`.
- `collection`: populated foreign sentinels never appear locally.
- `aggregate`: asymmetric foreign values contribute exactly zero.
- `mutation_relationship`: foreign input fails and before/after snapshots show zero
  row, event, quantity, balance, or state changes.
- `boundary`: adapter/tool context reaches an already classified shared service.
- `global_admin`: authority explains global scope and evidence proves the approved
  administrative boundary where externally reachable.

Existing tests count only when their named scenario explicitly asserts these semantics.
Each evidence reference MUST declare the operations it exercises, and the union of a
family's evidence references MUST cover every operation assigned to that family.
An unrelated passing happy path is not evidence.

## Baseline Gate

`003/FR-012` remains `Documented gap` until catalog validation, all named evidence,
representative adapter proof, full PostgreSQL tests, policy checks, and owner review pass.
No unrelated gap may change.
