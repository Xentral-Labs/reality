# Implementation Review: Global Command Palette

## Pre-implementation review — 2026-09-18

Product scope and planning were accepted in the conversation. The user authorized the grouping clarification and then requested continued work, authorizing implementation. The requirements checklist has 16 checked items; the reviewer-owned search-quality checklist retains its 24 unchecked markers. Continuing follows that explicit instruction; no reviewer approval is fabricated by changing markers.

The cross-artifact analysis found no critical/high findings. Its medium result-group ambiguity was corrected across spec, contracts, model, plan and tasks: eleven visible groups, four/twelve preview limits and merged fifty-row group pages. Targeted re-review confirms consistent group/provider separation and test coverage. All 32 requirement/criterion identifiers have task coverage. Constitution design rows remain PASS; no new business tables/fields or execution paths are introduced.

Architecture review: keep search predicates in tenant-scoped storage queries and application authorization in the shared service. API is transport-only. SQL support is installed by migration/test setup, never runtime startup. Migration changes are read access support over existing fields; preserve held data and exact identities. Recheck actual migration and performance evidence before final approval.

Checkout boundary: existing branch 234-inventory-cost-contribution contains unrelated chat/shell/spec225 and inventory-cost changes. Preserve them; do not stage, commit, reset or overwrite them. New feature work is limited to spec235 and the exact implementation paths needed for it. No merge/deploy authorization is inferred.

## Final review

Pending implementation and executable evidence.

## Measured database design refinement — 2026-09-18

The first disposable 100,000-item probe exceeded the 1,200ms statement timeout even for an exact SKU. Inspection showed the complete matching function was being evaluated across the tenant population. A subsequent complete regex prefilter plus equivalent ASCII normalization fast path still timed out without the migrated indexes. This is a failed performance probe, not SC-003 evidence.

Reviewed adjustment: retain the exact matcher as authority and add a complete single-edit regular-expression superset before it. Add PostgreSQL `pg_trgm` GIN expression indexes for human-label candidates, and normalized ID/reference B-tree access paths. No candidate sampling, derived business field, new business table, or changed match eligibility is permitted. `pg_trgm` must be installed by migration, never application startup. Rollback removes owned indexes/functions but retains the potentially shared extension. The deployment account requires extension installation rights; index build locking and write cost remain final-review items. This support-only adjustment keeps Constitution checks PASS and is driven by measured SC-003 failure. Full correctness and benchmark reruns remain required.

## Continuation findings

The working implementation is not release-ready. The authenticated ten-browser smoke
retains failed samples, and connection-pool exhaustion remains unresolved despite
nonblocking middleware authorization. No latency acceptance or complete story gate
is marked passed. Broader provider/browser coverage, final full-suite rerun and the
remaining requirement mapping still block completion.

Confirmed fixes include indexed equality predicates, nullable-field tier exclusion,
shipment EXISTS matching, label-order pagination independent of IDs, exhaustive
Latin-1 fast-path equivalence, and report draft/route preservation. Refer to the
verification log for exact commands and incremental results. Reviewer-owned checklist
markers remain untouched.

### Visual refinement review

User explicitly requested a modern, aligned appearance during searching. Scope is
loading/error presentation and layout, preserving provider retry and access policy.
Spec/plan/tasks are consistent; no unresolved clarification or critical finding.

Visual implementation review: loading aggregation and error disclosure preserve
provider-specific retries and successful results. Changes are scoped to the palette;
no matching, tenant authorization or business behavior changed. Desktop live typing,
308 frontend contracts, build and four-language audit pass. T058 remains open for
narrow-screen visual verification because native browser capture became unavailable.
Existing release blockers remain unchanged.

### Exact destination repair: requirements review and analysis

User-reported screenshot and live order inspection confirm register-surface child
rules strip the standalone Close button's padding and radius. The off-page order
preview also stretches short sections to the height of neighboring content.
FR-005/021 repair scope is accepted by the user's request. Spec, plan and T059–060
align; tests precede implementation. No clarification, schema change, constitutional
exception or critical inconsistency exists in this bounded repair. Existing broader
release gates remain open.

Follow-up live finding: Summit Bottle opened near the bottom of the master list
without bringing its detail into view. Revealing an opened exact selection restores
FR-005 destination visibility. Include the opt-in shared preview behavior in T059.

Final layout review: shared preview containment fixes the direct-child CSS collision.
Compact sections now use available container width in both inline and off-page
placements. Selection reveal waits for loaded content and is identity-bound, retaining
user scrolling on refresh. Sixteen live record-family examples plus 390px views were
inspected; missing fixture families are explicitly listed. 312 frontend contracts,
build and localization pass. No business reads/rules, authorization, schema or
mutation paths changed. Prior feature-wide performance/reliability gates stay open.

Palette consistency review: the user accepts the current layout and requests visual
alignment only. FR-010/021, the scoped plan and T061 agree; no open clarification or
critical finding. Existing sidebar/master-data glyphs and tokens are authoritative.

T061 final review: canonical IDs drive symbol choice; translated labels and search
behavior are untouched. Styling is palette-scoped and preserves 44px action targets.
Live visual comparison and existing frontend/policy checks passed.
