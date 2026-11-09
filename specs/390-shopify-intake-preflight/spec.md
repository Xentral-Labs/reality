# Feature Specification: Read-only Shopify intake preflight

**Feature Branch**: `390-shopify-intake-preflight`
**Created**: 2026-11-09
**Language**: English
**Status**: Bounded no-override read contract approved by parent coordinator

## User Scenarios & Testing

### Story 1 - Explain what remains after a reviewed existing buyer (P1)
A person asks Tuesday Main what is still needed for a retained Shopify order to
become a separately reviewed Reality intake. The read reports the exact retained
source and current reviewed buyer, then identifies missing company/location,
ambiguous or inactive SKU/item identity, unproved unit semantics and selected
financial/completeness evidence. It never chooses a reference or creates work.

Acceptance: an exact current source returns bounded, source-linked observations;
missing buyer/company/location is explicit; one active exact SKU is distinguished
from zero, inactive or ambiguous matches; stock unit is never treated as a source
sales-unit statement. No preparation or effect is accepted.

### Story 2 - A read must not silently use another source or imply readiness (P1)
A changed source pointer/hash/version, wrong job or foreign identity refuses before
publishing a current-looking report. A recorded buyer with changed customer basis
is historical/stale, not valid current mapping. More than100 source lines yields
explicit incomplete line coverage, never an all-lines readiness claim. Absent
interpreted line totals/delivery/unit fields describe selection/projection limits,
not proof that upstream Shopify lacks those facts.

Acceptance: stale pins refuse; report digest is stable across observation-time
changes but changes with semantic evidence; no SQL write is issued and persisted
source/job/action/business snapshots remain unchanged.

## Context and Intent

### Problem
Spec389 recognizes an existing buyer mapping but deliberately holds full intake.
The existing preparation service reads mappings only from immutable job.input and
would construct proposed effects; fabricating input or calling the old writer is
outside this read packet. SKU-first selection and implicit pcs/unit assumptions
must not become readiness evidence.

### Scope
One typed read-only MCP capability over exact tenant/source/job/hash/integer
version. Use canonical original GraphQL support validation, verified-buyer reader,
existing tenant record/role reads and completeness meanings. Diagnose retained
mappings only. Maximum100 returned lines and bounded serialized response.

### Non-Goals
Mapping overrides, reference selection or approval, master-data creation,
ImportJob.input/source mutation, PreparedIntake/Action/outcome creation, accepted
orders, provider calls, auto-preparation, payment/credit/stock/settlement readiness,
unit conversion, line-total recomputation, migrations, workers, UI variants or
actual old-runtime deployment.

## Requirements

- **FR-001** Accept only exact source_record_id/import_job_id/source_hash/positive integer source_version; tenant comes from authenticated transport. Validate latest original GraphQL source selection, order ID, job association and acquisition shop/query provenance.
- **FR-002** Read canonical verified buyer mapping and separate missing/current/stale state; retain the true approval Source/review link without exposing raw proof or inventing a customer.
- **FR-003** Diagnose only existing frozen company/location references. Require same-tenant active company role and active location, with shipping-location stock capability observed when applicable. Never choose a default or accept overrides.
- **FR-004** For each bounded supported source line distinguish missing SKU, no match, inactive, ambiguous active items and exactly one active item. Preserve original quantity as a string; return stock unit as observed and source unit as unknown, with no implicit conversion/defaultpcs.
- **FR-005** Report selected source support and financial/completeness limitations without inventing received totals/dates/units or claiming missing upstream facts. Payment, credit exposure, inventory, settlement and full business readiness remain not assessed.
- **FR-006** Return no more than100 lines, explicit total/returned/complete coverage, bounded typed codes and a semantic canonical digest excluding observed_at and itself. Reject an oversized report rather than silently truncating facts.
- **FR-007** Perform no persistent write or preparation; no SQL mutation, source/input change, proposal, effect or interpretation outcome. Both functional result and before/after persistence/SQL checks prove this.
- **FR-008** Expose through the normal narrow read tool and catalogues, with tenant isolation and explicit no-acceptance flags; no new model toolbar or privileged grant.
- **DR-001** Reuse current Source/Stream/Job, approved mapping evidence and existing master records. No schema addition or new persistent readiness state.

## Assumptions and Dependencies
Spec389 supplies the exact reviewed buyer relationship. The parent coordinator
approved a no-override read packet and owns the optional Tuesday Main consumer.
No actual provider/grant/deployment is authorized for this increment. Schema99
compatibility is not inferred from current-code tests; existing v3 deployed
capabilities do not automatically include this new read.

## Success Criteria
- **SC-001** A current mapped synthetic order produces an honest bounded diagnosis with no readiness/acceptance implication and zero persistence changes.
- **SC-002** Stale/foreign source and changed customer/reference/item tests fail closed or expose explicit stale/unknown status, without leaking another tenant.
- **SC-003** Unit/amount/coverage/size/digest edge cases and normal MCP/catalogue gates pass before completion; independent source review precedes commit.

## Requirement Traceability

| Requirements | Scenario | Planned proof |
| --- | --- | --- |
| FR-001/002/003 | Stories1/2 source and existing references | Exact/foreign/stale source, buyer and master record tests |
| FR-004/005 | Story1 honest selected meaning | SKU ambiguity/inactive/missing, unit unknown, amount and delivery coverage tests |
| FR-006/007/DR-001 | Story2 bounded immutable read | 100-line/size/stable digest and SQL/snapshot tests |
| FR-008 | Both stories normal integration | MCP permission, tenant catalogue and generated docs tests |
