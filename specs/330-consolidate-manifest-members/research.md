# Research: Receipt Manifest Membership

## Typed bounded union

Decision: one physical `cost_manifest_member` table, family-qualified opaque PK and five true nullable target columns constrained by a closed family shape. Rationale: the same manifest-membership grain and no incoming member FKs permit narrow consolidation, while all five target types remain real tenant-qualified references. Alternatives: keep five stores (no saving); JSON member lists or a single polymorphic target ID (loss of true FKs); consolidate all cost authorities (different grains and unproven history equivalence). Rejected.

## Exact-column logical write interfaces

Decision: five exact-original-column filtered views plus narrow INSTEAD OF INSERT routing. Native UPDATE/DELETE remains. Rationale: a filtered native view cannot supply a default to a hidden, unexposed underlying discriminator; exposing a discriminator would change original SQL columns, even if ORM fields and inspector output hide it. Existing cost projection defaults are useful precedent but do not satisfy this feature's stricter exact-column contract unchanged.

Insert routing must use fixed allowlisted branches and explicit columns, write the internally fixed family, obtain stored columns through RETURNING and return the correctly shaped NEW row. An INSTEAD OF INSERT trigger means view CHECK OPTION does not enforce that trigger's insert; the physical closed shape, fixed branch and FKs must enforce it. Native updates remain protected by the view predicate/check option and physical target checks. There is no SECURITY DEFINER or dynamic user-provided identifier. Test SQL/ORM flush, RETURNING, row counts and all original columns in PostgreSQL before acceptance. Alternative: expose routing column/default (violates exact column contract); adapt all services to direct physical writes (larger change and does not retain direct SQL inserts); general rule/trigger framework (unnecessary).

## Authority and lifecycle

Decision: no new mutation/admission guard. Rationale: original receipt members permit updates/deletes and corruption is detected by manifest hash verification. Later census/captured member guards are different contracts, not improvements to import incidentally. Original sorted target IDs and family keys remain the exact digest format. Existing late-cost/replacement/correction tests protect historical review results.

## Migration and metadata

Decision: freeze actual isolated predecessor DDL after 0088 key changes and migrations 0109–0111, confirm absence of incoming FKs and other SQL dependencies, lock/copy/bidirectional parity, then replace five tables with views and owned insert-routing function/triggers in one transaction. Downgrade restores current values and exact old DDL/indexes. Alternatives: live ORM-based migration or reconstructing from current decisions (not reproducible/lossless). Physical store/view metadata registration occurs before the FK index helper; logical views depend on storage and schema hooks create/drop only owned routing objects. Test repeated and partial metadata lifecycle and exclusion/count/purge helpers.

## Review

The speckit-plan research agent independently confirmed typed FKs, family-qualified identity, partial uniqueness, original mutable member behavior and actual predecessor DDL requirements. Its initial native view-default recommendation exposed an extra SQL discriminator and was rejected for FR-004; the follow-up independently accepted exact-column INSERT-only routing with native UPDATE/DELETE. It confirmed that INSERT CHECK OPTION does not enforce trigger writes, so physical checks/FKs and fixed-family branching are mandatory. It found no design blocker and requested explicit RETURNING/rowcount and partial metadata lifecycle proofs, which are planned. No implementation proof is claimed here.

A subsequent read-only concrete implementation architecture review found no actionable blocker: exact columns, invoker rights, seven typed FKs, closed shapes, native mutation, frozen rollback and normal metadata lifecycle match this design. Actual complete acceptance remains separate.
