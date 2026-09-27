# Implementation Plan: Governed ERP Logic Ownership

**Branch**: `spec/285-erp-logic-plan` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Make the existing ERP core independently auditable and resistant to duplicate business logic
without changing business behavior. Extend the existing executable catalogs into one deterministic
governance trace; validate singular command/read ownership, inward-only dependencies and no direct
adapter business writes; declare narrow, stale-checked exceptions; and prove the four approved
critical calculation families through shared cross-consumer business stories. Only after those
gates exist, split the two large application/MCP registration files at existing cohesive seams
behind compatibility-preserving facades.

The design deliberately does not attempt to detect generic "business arithmetic" by text. It names
the authoritative semantic question and owner for each critical calculation, prevents boundary
callers from reaching lower-level ingredients, and compares every registered consumer against the
same scenario vectors. Any existing disagreement blocks consolidation and returns to product/domain
review under FR-013.

## Technical Context

**Language/Version**: Python 3.12+; existing TypeScript consumers are inspected but no frontend feature is added
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI, Typer, pytest, Python AST; existing catalog/documentation generator
**Storage**: No persistence or business-schema change; governance metadata is deployment metadata derived from versioned executable catalogs
**Testing**: pytest unit, catalog planted-drift, architecture source fixtures, PostgreSQL service/business stories, adapter parity; existing Web/catalog checks and generated-doc checks
**Project Type**: shared backend core with Web/API, CLI, Chat, MCP, worker, scheduler, integration and demo adapters
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope; Source → Evidence → Reality; no public contract or business-semantic change
**Scale/Scope**: All catalogued ERP commands and public ERP reads receive structural governance; semantic consolidation is limited to inventory availability, commitment fulfilment/open quantity, open financial balances and contribution results

There are no unresolved technical clarifications. [research.md](research.md) records the selected
mechanisms and rejected alternatives.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Governance describes current provenance and ownership only; `data-model.md` keeps trace metadata outside business authority. Critical stories begin with retained Reality/evidence and compare read-time observations. | PASS |
| Reality owns operational state | No document status or substitute state is added. Inventory, fulfilment, balances and contribution remain derived from Movements/Reservations/Commitments/LedgerEntries and reviewed cost evidence. | PASS |
| Proven schema only | No database field, table, migration or backfill is introduced. New metadata is version-controlled deployment/catalog metadata needed by FR-001–FR-018. | PASS |
| Tenant + shared service boundaries | Architecture validation prohibits direct adapter business writes and reversed layer imports; cross-consumer stories run through tenant-scoped canonical owners and existing tools. | PASS |
| Spec/test traceability | The table below maps every FR/DR to a named initial failing proof; tasks must preserve this map and tests precede implementation. | PASS |
| Explainable web behavior | Public behavior is unchanged. Generated governance reference exposes owner, basis/effects, consumers and evidence; Web continues to consume shared reads/services. | PASS |
| Received values not recomputed | Finance and contribution stories retain source-stated amounts; derived observations are calculated at read time and never persisted as new authority. | PASS |
| Smallest coherent design | Reuses current catalogs, handlers and tests; adds one pure validator/composer layer and four bounded parity matrices. No rules engine, generated handlers, new public tool or schema. | PASS |

Post-design re-evaluation: all rows remain PASS. The contracts add no new authority or external
mutation surface, and the data model is metadata-only. Planning may proceed to tasks after review.

## Repository Structure and Layer Changes

```text
packages/reality-core/config/
├── command_catalog.yaml                   # owner/evidence declarations in existing authority
├── resource_catalog.yaml                  # unchanged business grouping; validated by trace
└── erp_boundary_exceptions.yaml           # narrow path/function/rule/rationale/evidence only

packages/reality-core/src/reality/
├── catalogs.py                            # compose/validate governance trace with existing catalogs
├── governance.py                          # pure trace and architecture-validation model
├── tools/
│   ├── registry.py                        # Tool contract + ordered duplicate-refusing composition
│   ├── application.py                     # stable facade; proposal lifecycle and dispatch remain here
│   └── registrations/
│       ├── finance.py
│       ├── costing.py
│       └── analytics.py                   # first cohesive extraction seams only
└── mcp/
    ├── definitions.py                     # dependency-light definition/building primitives
    ├── catalog.py                         # stable facade/final registry/dispatch compatibility
    └── registrations/
        ├── operations.py
        ├── finance.py
        ├── costing.py
        └── analytics.py

packages/reality-core/tests/
├── test_erp_governance.py                 # trace completeness + planted catalog/AST drift
├── scenarios/test_erp_calculation_parity.py # four shared cross-consumer scenario matrices
├── test_application_catalog.py            # strengthened unique-owner/catalog checks
├── test_tool_catalog.py                    # exact ordered metadata compatibility
└── test_agent_command_parity.py            # public-to-application binding compatibility

apps/docs/scripts/generate-catalog-reference.py # generated governance reference
apps/docs/content/tool-usage/governance.md       # generated, externally readable trace/audit index
apps/docs/.vitepress/data/tool-usage.json        # generated payload
docs/ARCHITECTURE.md                              # durable ownership/layer rule
docs/features/erp-logic-governance.md             # durable governance and audit contract
specs/285-erp-logic-governance/review.md           # final inspected scope/discrepancy record
```

**Dependency direction**: `domain <- services <- tools <- adapters`. Registry fragments depend on
dependency-light contracts and business handlers, never on adapter modules. `tools/application.py`
and `mcp/catalog.py` remain stable import facades. Services importing tool internals are audited;
the private opening-stock evidence leak is moved to its owning service before the relevant fragment
is extracted, while broader historical orchestration imports are classified individually rather
than hidden by a blanket exception.

## Design

### Governance trace

`reality.governance` builds one immutable trace from the already loaded application catalog, tool
registry and MCP registry. It does not scan runtime business data. For each command it treats the
catalogued primary `service` as the authoritative application owner; `related_services` are
supporting operations and cannot become a second owner. For a public read without a business
command, capability guidance supplies the canonical `application_tool` and its data basis,
limitations and verification meaning.

The existing command and capability-guidance entries gain executable-evidence references in their
own canonical blocks. Evidence is not maintained in a parallel inventory. The trace joins:

- business resource and process membership from `resource_catalog.yaml`;
- command owner, mode, adapters, reads/writes, effects and events from `command_catalog.yaml`;
- public bindings and schemas from the MCP/application registries;
- verification reads and limitations from capability guidance;
- exact executable test node identifiers declared beside the governed entry;
- explicit exclusions for transport/operational helpers with a reason.

Validation refuses duplicate command services, missing or duplicate mutation owners, unknown/stale
tools or tests, unclassified public reads, conflicting resource ownership, nondeterministic
composition and unexplained exclusions. Diagnostics name the capability, conflicting/missing owner
and expected boundary. The generated docs render the same validated trace; they do not keep a
second list.

### Architecture enforcement

One pure validator accepts source roots and catalog fixtures so tests can plant drift without
editing production files. It uses Python AST for deterministic rules:

1. `domain` imports neither services, tools nor adapters; services import neither tools nor
   adapters; tools import no adapter.
2. Governed adapter/runtime areas do not call SQLAlchemy business mutations or Core DML against
   business models. A commit or a database import alone is not treated as a write.
3. Critical-calculation consumers call their named owner or an approved composition and do not
   import/call the lower-level ingredients in order to reconstruct the result.
4. Each exception is path-, function- and rule-scoped, carries rationale and executable evidence,
   and fails when unused or when its target changes.

The validator includes positive controls for permitted transport-shape validation, authorization,
tenant selection, formatting and presentation-only arithmetic. Generic similarity or arithmetic
matching is explicitly not a completion claim.

### Registry composition

Registration is modularized only after singular ownership/architecture validation is green.
Ordered fragment composition rejects duplicate names rather than allowing later dictionary writes
to overwrite an earlier definition. The first split follows existing coherent seams—finance,
costing and analytics/graph for application tools; operations, finance, costing and analytics for
MCP definitions. Core proposal preparation, preview, approval/execution, transaction/confirmation
policy and dispatch stay in `tools/application.py`.

Compatibility snapshots compare, in order:

- every application tool name, mutating flag and description;
- every MCP public name, description, access, group, input schema and application binding;
- tool/catalog object shape and stable facade imports;
- proposal review classification, authorization and generated documentation.

The final facade registries remain mutable because existing authorization and test code consume or
patch them. Internal fragments are immutable. Existing group strings, including capitalization,
are preserved; cleanup is out of scope.

### Four critical calculation owners and parity

Ownership is declared per semantic question and grain, not by pretending different questions are
one function:

1. **Inventory availability** — `services.inventory_positions.inventory_detail_rows` owns exact
   dimensional positions; `services.core.inventory_rows` owns the operational item/location
   register; existing scalar primitives support mutation guards. A parity invariant proves that
   exact positions aggregate to the operational grain and that projection/tool/readiness/exception
   consumers preserve physical, reserved, available, incoming and projected meanings.
2. **Commitment fulfilment/open quantity** — `services.core.commitment_terms` (and its scalar
   primitives) becomes the named semantic owner for effective quantity, fulfilled and clamped open
   quantity. Correlated list expressions, readiness, projections and exceptions must reuse an
   admitted expression/owner rather than restating revision/correction rules. This is the first
   consolidation slice because current risk is highest.
3. **Open financial balances** — `services.core.settlement_positions` owns invoice open amount;
   `services.finance.balances.party_balance_rows` owns party/currency totals including unused
   credit. The distinction is retained and parity covers scalar, bulk, aging, projections,
   dunning/exceptions and public reads without cross-currency netting.
4. **Contribution results** — `domain.contribution.aggregate_contribution` owns DB arithmetic;
   candidate and reviewed services own their distinct authority/freshness states. Preview, reviewed
   results, cost queries, generations/captured reports and negative-DB1 exceptions must preserve
   the canonical arithmetic and the same unknown/stale state instead of collapsing those states.

Each scenario vector names its evidence cutoff and exercises direct owner plus every registered
consumer. A consumer added later must join the matrix through the governance trace. Disagreement
creates a failing audit row in `review.md`; no implementation may select a winner without a new
approved clarification.

### Reality flow

No business flow changes. Tests construct the existing shortest paths:

```text
SourceRecord -> Document/DocumentLine -> Commitment -> Reservation/Movement
SourceRecord -> Document/DocumentLine -> LedgerEntry -> SettlementAllocation/Reversal
received revenue + reviewed acquisition/selling evidence -> read-time contribution observation
```

Governance records references to the owners and proofs only. It neither stores a business value nor
becomes permission, evidence, operational state or a projection used to authorize a mutation.

### Service and adapter flow

```text
Web / API / CLI / Chat / MCP / worker / scheduler / integration / demo
                              |
                    stable application tool/service
                              |
                named semantic owner / domain rule
                              |
             tenant-scoped repositories and PostgreSQL
```

Adapters retain authentication, authorization transport, serialization and presentation. Existing
mutation confirmation, proposal claim/replay and locks remain where they are. The architecture gate
proves the path; it does not introduce a second dispatcher.

### Data and migration impact

No Alembic migration, persisted entity, backfill, business-table write or API payload is added.
`CapabilityTrace`, `Ownership`, `BoundaryException` and calculation-consumer declarations are
version-controlled deployment metadata described in [data-model.md](data-model.md). Catalog startup
remains fail-fast and atomic; a broken trace prevents readiness rather than exposing a partial
catalog.

### Failure, security, and tenant behavior

- Catalog/architecture failures are deterministic developer failures and contain repository paths,
  capability identities and rule names, never tenant data or source payloads.
- Runtime authorization, tenant selection and confirmation are unchanged and remain server-owned.
- Cross-consumer stories use two tenants where the underlying read is tenant-sensitive and assert
  not-found/non-disclosure behavior already required by the tenant catalog.
- Evidence node IDs are repository references, not executable user input.
- Exceptions cannot be activated by conversation or runtime configuration; they require reviewed
  repository change and their own executable positive proof.
- Unknown/stale calculation state is compared as a first-class outcome; validators never replace it
  with zero, false or a locally computed fallback.

## Test Strategy and Traceability

Tests are added first and observed failing where practical. Catalog/AST tests use tiny injected
fixtures for precise diagnostics; semantic parity uses PostgreSQL business stories and existing
public tools/services. Existing suites remain regression evidence, not substitutes for the new
cross-consumer matrices.

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-003 | catalog/unit | `tests/test_erp_governance.py::test_every_governed_capability_has_one_complete_trace` plus missing/duplicate/stale owner fixtures | No complete trace/evidence declaration and duplicate command services are not rejected today |
| FR-004–FR-007 | architecture/unit | planted adapter write, reversed import, local calculation and stale/narrow exception cases in `test_erp_governance.py` | No unified business-write/layer validator exists |
| FR-008–FR-010 | registry/contract | ordered fragment duplicate/missing fixture and before/after public metadata snapshots in `test_tool_catalog.py` and `test_agent_command_parity.py` | Application registry currently permits overwrite and both registries are monolithic |
| FR-011–FR-013 | PostgreSQL story | four parametrized matrices in `scenarios/test_erp_calculation_parity.py` | Fulfilment/inventory consumers use multiple formula paths and no complete matrix exists |
| FR-014–FR-016 | catalog/unit | new capability without owner/evidence/exclusion and unused exception planted drift | Current catalogs do not require governance evidence or stale exception proof |
| FR-017 | regression/integration | tenant isolation, proposal review, MCP permissions, demo entrypoint parity, fulfillment safety and financial/contribution suites | Must remain green; any failure is a regression rather than intended change |
| FR-018 | review/docs | `review.md` completeness check plus generated governance page/catalog freshness | No bounded external audit record exists |
| DR-001–DR-003 | story/catalog | provenance and received-vs-derived assertions inside four matrices; no persistence model/migration diff | Existing behavior is distributed rather than proven by one audit |
| DR-004–DR-007 | architecture/parity | two-tenant stories, inward import gate, adapter/demo/worker consumer coverage | Automated callers are not currently part of one ownership proof |

Focused existing regression suites include:

- `tests/test_application_catalog.py`, `test_capability_guidance.py`,
  `test_action_discovery.py`, `test_agent_command_parity.py`, `test_tool_catalog.py`;
- `tests/tenant_isolation/`, `test_mcp_permission_parity.py`,
  `test_proposal_review_parity.py`, `test_demo_entrypoint_parity.py`;
- `tests/scenarios/test_fulfillment_safety_parity.py`,
  `test_inventory_and_fulfillment.py`, `finance/test_party_balances.py`,
  `test_contribution*.py`, operational exception tests;
- `make docs-generate`, `make docs-catalog-check`, `make spec-check`, backend lint/format and the
  complete PostgreSQL test suite.

## Rollout and Rollback

Deliver in reversible slices: (1) governance trace and diagnostics, (2) architecture gates and
exceptions, (3) four semantic audit matrices and any behavior-preserving owner reuse, (4) registry
composition and first fragment extraction, (5) generated reference/final review. Each slice keeps
public facades and behavior green. No runtime feature flag or data rollout is needed.

Rollback reverts code/catalog/docs because there is no migration or stored state. A registry split
can be rolled back independently to the stable facades. A semantic consolidation is reverted only
with its parity tests intact; if a discovered discrepancy lacks domain approval, that slice is not
merged rather than hidden behind a compatibility switch.

## Review Risks

- **False confidence from static scanning**: AST proves named boundaries, not semantic equality;
  behavioral matrices are mandatory for the four calculations.
- **False positives**: existing adapters legitimately perform technical writes and formatting;
  rules target business models/operations and require positive controls plus narrow exceptions.
- **Fulfilment semantic drift**: revisions, corrections, cancellation, over-fulfilment and returns
  differ subtly across current formula paths; disagreement blocks the slice.
- **Inventory grain collapse**: item/location and lot/serial/handling-unit positions are related but
  not interchangeable; aggregation parity must not erase unknown dimensions.
- **Finance meaning collapse**: invoice open amount, unused credit, party net balance and account
  balance remain separate semantic questions.
- **Contribution authority collapse**: candidate, reviewed, stale and unknown results must not be
  treated as equivalent merely because they share arithmetic.
- **Registry import cycles/order drift**: stable facades, dependency-light definitions and exact
  ordered snapshots gate extraction.
- **Large metadata migration**: adding evidence to every governed capability is review-heavy;
  generated coverage and exact test-node validation prevent empty ceremonial declarations.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
