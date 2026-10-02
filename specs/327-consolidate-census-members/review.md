# Implementation Review: Census Membership

Reviewed against all 11 FR, three DR and eight Constitution checks. Runtime acceptance
is recorded separately in verification.md; this review does not replace CI evidence.

- FR-001/SC-001: four physical families become one; exact metadata inventory is 150
  physical tables and 25 views on current main, a three-table census reduction.
- FR-002/004, DR-002: family-qualified PK preserves opaque equal IDs; closed shape
  rejects missing/wrong subjects; ordinary nullable generated aliases preserve real
  document/line identity without duplicated consumer fields.
- FR-003: all eight backing FKs are real tenant-qualified relationships. Self-reference
  includes census; incoming company input selects only a line alias. Complete FK
  indexes are checked on actual migrated PostgreSQL and metadata schema.
- FR-005/007, DR-001: exact original view fields/order, stored RETURNING, unchanged
  serializers, observations, hashes, cursor/replay and canonical service entrypoints.
- FR-006/008, DR-003: physical guard covers both direct and view writes, locks the
  building parent and preserves member immutability. Both admission/seal race orders
  observe actual blocking. Original header function/trigger remains unchanged.
- FR-009/SC-002: migration freezes actual predecessor DDL, locks deterministically,
  copies documents before lines, verifies both EXCEPT directions, redirects consumers
  and installs guards before commit. Populated downgrade restores all original keys,
  index binding, functions and data; parity failure is transactional. No CASCADE,
  live-model imports or constraint disabling occurs.
- FR-010: metadata dependencies and owned-function cleanup support repeated/selected
  lifecycle. Existing count/purge services skip logical views and visit physical rows
  once. Protected-history refusal/rollback and another tenant remain intact.
- FR-011/SC-003: no source payload, Evidence, Finance decision, authority row or public
  service/tool/adapter field changes. Source absence remains absent; no derivation is
  persisted as authority and no permission/confirmation boundary is bypassed.

Implementation stays inside existing storage and test boundaries. All repository
artifacts are English. No generic Settings registry, background subsystem or schema
expansion outside the reviewed membership use case is introduced.

Historical c76 closing review: specs 331/332 retain upstream specs 328/329; migration
0116 follows upstream 0115, and 0120 is the only head. Exact physical/view inventory,
all 926 frozen hashes and final runtime evidence were reconciled. Test-only async
waiting matches the existing Finance rollout contract without changing business
assertions or the serial performance limit. All required gates passed before T019–
T021 were marked complete. Closing changes affect documentation/evidence only.

Currency integration review: upstream company_currency is retained; the current
metadata has 150 physical tables and 25 views, compared with 168 before this PR.
The eighteen-table reduction is unchanged. Frozen predecessor member DDL remains
exactly equal on revision 0120_manifest_members; 0121 is the only migration head.
