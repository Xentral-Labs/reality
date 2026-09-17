# Graph-Native Reporting Design Review

Date: 2026-09-17. Scope: specification and planning artifacts only.

## Accepted direction

The owner rejected all three previous shapes of Analytics in turn — filter and
configuration, the bespoke SQL subset, and user-authored native SQL — and accepted a
declared property graph over the existing typed tables, traversed by a query the system
can check before it runs. PostgreSQL remains the engine. No migration, role, view,
database object or second engine was created.

The decisive objection to the previous revision came from the owner: having to publish
every relation as a static view beforehand contradicts the promise of asking anything.
That objection is correct, and it identified a real contradiction. The views existed only
because user-written SQL text needs a boundary inside the database, and the specification
forbade a view per report, so the views could only be raw relations — which left every
join to be re-derived per question with nothing able to check it. The result would have
had the ceremony of pre-declaration and the unverifiability of free text at once.

## Withdrawn from the previous revision

- User-authored SQL in the primary path.
- Barrier views, per-tenant database roles, PUBLIC-grant provisioning and the session
  authorisation design. ADR 0004's tenant count no longer constrains this feature through
  role lifecycle, because no role per tenant is created.
- Engine selection as a delivery gate. It survives as a deferred measurement with an
  explicit trigger, which is safe precisely because the stored query form carries no SQL
  dialect.

These were not mistakes of execution; they were the necessary consequences of the earlier
premise. Removing the premise removes them.

## Design checks

- Grain, multiplicity and additivity are declared once per node, edge and measure, which
  is the minimum a traversal engine needs and the maximum it can be given. Everything
  else about a query stays free.
- The fan-out rule is structural, not advisory. The compiler computes the effective grain
  of a path and folds or refuses. Cypher and hand-written SQL both return the multiplied
  total here, and the counterexample is recorded in the same fixtures.
- The trust boundary returns to the compiler, where every other tenant-scoped read in the
  product already enforces it. The adversarial suite asserts the emitted predicate on
  every node, including inside recursive common table expressions and separate branches.
  Row-level security stays available as independent defence in depth.
- Graph databases were evaluated and rejected on exact decimals, tenant isolation at
  roughly 5,000 tenants and workload shape, with Apache AGE rejected additionally because
  it stores its own copy. SQL/PGQ is the standardised form of this design and should be
  re-checked when it reaches PostgreSQL core.
- The Cypher divergence in `RETURN` is deliberate and documented. Adopting Cypher
  aggregation wholesale would reimport the defect the model exists to remove.
- Extension is by declaration, including recursive edges. `location.parent_location_id` is
  the only recursive edge today; bills of material, nested handling units and party
  hierarchies are anticipated and cost a configuration row when they arrive.
- Temporal history and generic exact lineage are still not claimed. The traversal path is
  the derivation; unsupported historical modes fail explicitly.
- No security proof has been executed. T006 and T007 remain mandatory before exposure,
  and a failed proof requires design revision rather than a bypassed gate.

## Documentation verification

`python3 scripts/check_spec_policy.py`: passed.
These are documentation checks only — not backend, migration, browser or performance
tests. No implementation task is marked complete. Spec 222's deployed Q01 evidence is
unchanged, and its unimplemented compiler-expansion roadmap continues to point here.

## Working tree note

Another session is active in this working tree; artifacts in this feature changed on disk
during the previous revision. The superseded revision is preserved outside the repository
before this rewrite. The feature directory keeps its existing name to avoid a split
directory while a second session may be writing; renaming it to match the new title is a
separate, deliberate step.

## Next executable step

T001 cross-artifact analysis, then T002 declaration validation tests. Do not extend
`sql_compile.py` for joins and do not add a barrier view or a reporting role while this
replacement is being prepared.
