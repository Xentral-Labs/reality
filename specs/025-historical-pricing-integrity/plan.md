# Implementation Plan: Historical Pricing Integrity

**Branch**: `025-historical-pricing-integrity` | **Date**: 2026-09-02 | **Spec**: [`spec.md`](spec.md)

**Language**: English for all repository artifacts and review evidence.
**Status**: Specification, plan, implementation, and final review approved by the product owner on 2026-09-02.

## Summary

Close the `004/FR-014` gap by treating each DocumentLine's stored commercial values as
the immutable agreement snapshot and its optional `price_list_entry_id` as the shortest
explanation link. Extend the existing shared manual DocumentLine creation boundary with
an optional selected-entry ID that is accepted only after the existing resolver
reproduces the complete commercial context. Add focused before/after PostgreSQL stories for every supported
pricing configuration change, one shared historical-pricing explanation read, and a
small Inspector presentation. Do not add tables, fields, a pricing version aggregate,
or retroactive repricing behavior.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript where frontend is in scope
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite as applicable
**Storage**: PostgreSQL; immutable object storage only for proven source binaries
**Testing**: pytest business stories/integration/unit; frontend build and focused UI tests
**Project Type**: backend services/API/CLI plus independent frontend
**Constraints**: Decimal; UTC; opaque IDs; lossless source; strict tenant scope
**Scale/Scope**: One baseline gap; existing pricing and Evidence entities; focused backend/API/Inspector proof; no public Site work

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Price configuration informs an agreement; DocumentLine preserves Evidence; existing Commitment/Movement/LedgerEntry links remain unchanged. | PASS |
| Reality owns operational state | No delivery, inventory, fulfillment, or finance status moves onto Document or pricing records. | PASS |
| Proven schema only | Existing agreed line values and optional PriceListEntry FK are sufficient; schema expansion is prohibited. | PASS |
| Tenant + shared service boundaries | Resolution and explanation remain tenant-scoped shared services; API and Inspector only transport/present them. | PASS |
| Spec/test traceability | Every FR/DR maps to a named before/after, effective-time, tenant, failure, or Inspector proof below. | PASS |
| Explainable web behavior | Document Inspector leads with agreed Evidence and labels the retained entry separately from a fresh current resolution. | PASS |
| Smallest coherent design | Focused proof plus one read model reuses current pricing; no event, migration, mutation, or parallel engine. | PASS |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/domain/       # pure rules, if needed
packages/reality-core/src/reality/services/     # application behavior
packages/reality-core/src/reality/tools/        # shared agent/CLI tools
packages/reality-core/src/reality/web/          # transport only
packages/reality-core/tests/                    # unit, service, story, adapter proof
apps/web/src/                     # presentation only
provider-site/src/                    # public presentation only, when in scope
```

**Files/layers affected**:

```text
specs/025-historical-pricing-integrity/             # approved requirements/design/evidence
packages/reality-core/src/reality/services/core.py  # shared read-only historical explanation
packages/reality-core/src/reality/web/api.py         # optional line input and Inspector/API presentation only
packages/reality-core/tests/test_pricing.py          # historical non-rewrite/effective-time stories
packages/reality-core/tests/test_master_data_api.py  # tenant-safe Inspector/API proof
packages/reality-core/tests/test_spec_policy.py      # baseline-gap closure regression
docs/features/operational_fields.md                  # pricing-history contract clarification
docs/WEB_SPEC.md                                     # agreed-vs-current Inspector wording
docs/SPEC_COVERAGE_MATRIX.md                         # close only 004/FR-014 after approval
specs/004-master-data/spec.md                        # mark only FR-014 verified after final gate
```

Dependency direction remains UI/API → shared service → tenant-scoped records.

## Design

### Reality flow

PriceList, PriceListEntry, direct assignments, group memberships, and group assignments
are commercial configuration used for a decision. DocumentLine stores the resulting
agreed quantity, unit price, gross amount, unit, and optional PriceListEntry identity as
Evidence. Existing Reality continues through DocumentLine/Document to Commitment and
through normal posting/fulfillment paths to Movement and LedgerEntry.

The shortest historical explanation is:

```text
DocumentLine → selected PriceListEntry → PriceList
```

The line does not copy list, assignment, group, or source relationships. A manual line
without a selected entry remains valid Evidence.

### Service and adapter flow

Extend the existing shared manual DocumentLine input with an optional selected-entry ID.
Before persisting the Document and its lines, the service derives direction and
business-effective time from the Document context, calls the existing resolver with the
line's party/item/quantity/currency/unit, and requires the exact entry identity and unit
price to match. Missing/manual identity remains allowed. Any mismatch or foreign ID
rejects the whole existing atomic creation transaction.

Add one tenant-scoped read operation that returns:

- the agreed DocumentLine values;
- the retained selected entry and parent list when present;
- whether the selected configuration is currently applicable for an explicitly supplied
  comparison time;
- a fresh resolution for the same commercial inputs when enough inputs exist;
- an explicit distinction between `agreed` and `current_resolution`.

The service calls the existing `resolve_price` implementation for the comparison and
never persists its result. The document Inspector consumes this shared read. Transport
code does not infer price history or overwrite Evidence. Existing price mutations remain
unchanged and therefore cannot acquire a hidden repricing side effect.

### Data and migration impact

No schema or migration change. `DocumentLine.unit_price`, `gross_amount`, `quantity`,
`unit`, and `price_list_entry_id` already represent the agreed Evidence boundary.
`PriceListEntry` remains historically readable. A schema diff is a failing review
condition for this feature unless the spec and plan are explicitly reopened.

### Failure, security, and tenant behavior

Every line, selected entry, list, party, and item lookup includes the tenant boundary.
A foreign line or entry behaves as not found. A malformed retained relationship is
reported as unavailable rather than reconstructed from human values. Explanation is
read-only and idempotent. Existing mutation transactions and rollback behavior remain
unchanged; tests snapshot Evidence and Reality before attempted invalid changes and
compare them afterward.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-003, FR-013 | PostgreSQL business story | `tests/test_pricing.py::test_selected_entry_attachment_is_server_validated_and_historical` | Existing suite resolves prices but no service can retain the selected identity on a new line. |
| FR-004–FR-005 | PostgreSQL effective-time story | `tests/test_pricing.py::test_old_and_new_work_use_their_own_effective_pricing_context` | No test compares retained Evidence with later direct/group/default/tier results. |
| FR-006, FR-008–FR-009 | PostgreSQL domain story | Manual line plus opaque-link and sales/purchase separation tests in `test_pricing.py` | Existing tests do not prove manual Evidence or same-value/different-identity history. |
| FR-007 | Service/API story | Historical explanation and Document Inspector assertions in `test_master_data_api.py` | Inspector currently shows agreed totals but not retained pricing identity or current comparison. |
| FR-010, FR-013 | Two-tenant service/API story | Foreign/mismatched line-entry attachment plus reference non-disclosure in pricing and API tests | Existing price resolution is scoped, but no supported attachment/explanation boundary exists. |
| FR-011 | PostgreSQL failure story | Before/after Evidence and Reality snapshot around rejected pricing changes | No focused non-mutation snapshot exists. |
| FR-012, DR-001–DR-005 | Contract/policy review | Shared-service call-path assertion, schema diff, documentation and Spec policy | The baseline gap remains explicitly open today. |

## Rollout and Rollback

The change is additive at the read/test/documentation level and requires no data
migration. Existing API fields and pricing behavior remain compatible. Rollback removes
the new explanation fields/service and focused tests; no stored business data requires
reversal. `004/FR-014` is closed only after the full suite and owner final review pass.

## Review Risks

- Accidentally treating today's resolution as the historical agreement.
- Mutating or replacing an existing PriceListEntry that is retained by a DocumentLine.
- Claiming a source or assignment was historical when only the selected entry is known.
- Recreating a relationship from matching amount, SKU, list code, currency, or unit.
- Expanding this proof into discounting, price-version management, or adapter equivalence.

Post-design Constitution re-evaluation: PASS. No exception is required.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
