# Research: Governed ERP Logic Ownership

## R1 — Combine catalog, AST and behavioral proof

**Decision**: Use executable catalog validation for ownership/evidence, AST source validation for
dependencies and direct business writes, and shared PostgreSQL scenarios for semantic parity.

**Rationale**: No one mechanism proves all requirements. Catalog validation is precise for declared
identity, AST is deterministic for forbidden dependencies and write calls, and only business
stories prove that different consumers calculate the same meaning and unknown state.

**Alternatives considered**: Regex or generic arithmetic similarity is noisy; runtime monkeypatching
covers only executed paths; an import-linter cannot prove writes, ownership or arithmetic parity; a
custom lint plugin adds packaging cost without improving the focused gate.

## R2 — Extend current authorities, not a parallel inventory

**Decision**: Derive the trace from current command/resource/process/tool/MCP catalogs. Put
executable-evidence references beside the existing command or capability-guidance entry. Treat
command `service` and read `application_tool` as ownership declarations.

**Rationale**: These catalogs already drive runtime validation and public docs. A second mapping
would drift. The missing controls are uniqueness, evidence and joined presentation.

**Alternatives considered**: A standalone ownership spreadsheet/YAML was rejected as duplicate
authority; import-graph inference cannot express business intent; calculations do not move to YAML.

## R3 — Scope exceptions narrowly and make them decay

**Decision**: An exception names exact rule, path, function, rationale and executable evidence.
Validation fails when it no longer matches an offense or its target disappears.

**Rationale**: Legitimate technical writes and historical orchestration boundaries exist. Whole-file
allowlists would permanently hide later business logic.

**Alternatives considered**: Banning every adapter session/commit is wrong because commit alone is
not a business write; permitting whole legacy modules is too broad; forbidding all exceptions would
force unrelated behavior changes into this feature.

## R4 — Preserve facades and split only after governance

**Decision**: Keep `tools/application.py` and `mcp/catalog.py` as stable public facades and dispatch
owners. Add deterministic duplicate-refusing fragment composition, then extract only coherent
finance, costing and analytics/operations seams. Proposal lifecycle stays in the facade.

**Rationale**: Tests/adapters import and patch the final registries; order, mutability and schema
output are compatibility constraints. Governance must establish singular ownership first.

**Alternatives considered**: One `erp_logic.py` creates a worse monolith; YAML-generated handlers
obscure policy; display groups do not align with ownership; moving proposal lifecycle raises
transaction risk; filesystem auto-discovery is nondeterministic; immutable public registries would
break compatibility.

## R5 — Own inventory by semantic grain

**Decision**: Retain separate owners for exact dimensional positions and the operational
item/location register, with an aggregation invariant and shared consumer scenarios.

**Rationale**: Lot/serial/handling-unit positions and operational stock/supply answer related but
different questions. Collapsing them erases meaningful unknown dimensions.

**Alternatives considered**: One universal row shape is a semantic/performance expansion; repeated
caller-side `physical - reserved` remains vulnerable to correction/status drift.

## R6 — Consolidate fulfilment first

**Decision**: Name `commitment_terms` and its admitted scalar/expression primitives as the canonical
meaning of effective, fulfilled and clamped open quantity. List, readiness, projection and exception
consumers reuse that meaning and one shared matrix.

**Rationale**: Current code has at least four formula paths. Revisions, corrected movements,
cancellation and over-fulfilment make this the highest immediate risk.

**Alternatives considered**: Independent optimized formulas retain several owners; scalar per-row
calls may regress performance, so shared batch/expression primitives remain permitted.

## R7 — Preserve two finance questions

**Decision**: Keep settlement/open-invoice positions separate from party/currency totals including
unused credit, and prove each consumer against its appropriate owner.

**Rationale**: Finance is already most centralized. Invoice open, credit, party net and account
balance are not interchangeable and currencies must not be netted together.

**Alternatives considered**: One generic balance service would collapse intentional distinctions.

## R8 — Preserve contribution authority states

**Decision**: Keep `aggregate_contribution` as arithmetic authority while candidate/reviewed
services own different evidence and freshness states. Parity includes unknown/stale outcomes and
the negative-DB1 exception.

**Rationale**: Shared arithmetic does not make a candidate financial authority. Drift risk lies in
state/presentation, captured replay and local partial exception arithmetic.

**Alternatives considered**: One universal contribution result would blur confirmed, candidate,
stale and unknown authority.
