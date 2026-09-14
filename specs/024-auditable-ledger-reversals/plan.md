# Implementation Plan: Auditable Ledger Reversals

**Branch**: `024-auditable-ledger-reversals` | **Date**: 2026-09-01 | **Spec**: [spec.md](spec.md)
**Status**: Specification and plan approved by the product owner on 2026-09-01
**Language**: English for all repository artifacts and review evidence.

## Summary

Close `012/FR-008` with one tenant-scoped service that locks a complete immutable
posting group, appends an exact inverse group, records one `LedgerReversal` relation and
one `ledger.reversed` event, and commits once. A shared active-allocation predicate makes
allocations touching reversed groups historical but operationally inactive. Every
finance view, exception, projection, API, CLI, application tool, MCP proposal, and Web
surface delegates to this meaning and exposes preview plus explicit confirmation.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript for the existing Web product
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, Typer, React/Vite
**Storage**: PostgreSQL with existing LedgerEntry/SettlementAllocation plus one reversal relation
**Testing**: pytest service/story/API/CLI/tool/isolation; migration checks; Ruff; Web build/i18n/manual review
**Project Type**: shared Python core with API/CLI/MCP/Chat adapters and React Web
**Constraints**: Decimal; UTC; opaque posting-group IDs; immutable entries/allocations/source; tenant scope; one transaction
**Scale/Scope**: One complete group and its allocations per operation; no partial, bulk, replacement, period, or benchmark scope

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Original Entry → Document/Source remains unchanged; LedgerReversal is direct correction Evidence and inverse entries reach original business Evidence through it without copying provenance. | PASS |
| Reality owns operational state | Entries and allocations remain authority; reversal and active settlement state are derived without Document status. | PASS |
| Proven schema only | Relation fields are used for uniqueness, locking, retry, allocation filtering, role display, events, and explanation. | PASS |
| Tenant + shared service boundaries | One tenant-explicit service owns snapshot, preview, execute, relation, event, and commit; all adapters delegate. | PASS |
| Spec/test traceability | Every FR/DR maps to planned failing evidence below. | PASS |
| Explainable web behavior | Journal roles and Inspector traverse original/reversal, Evidence, allocations, reason, actor/time, net effect, and event. | PASS |
| Smallest coherent design | Existing entries, opaque group identity, allocation rows, event/proposal systems, and views are reused; one table/event are added. | PASS |

Post-design re-evaluation: PASS. No Constitution exception is required.

## Repository Structure and Layer Changes

```text
packages/reality-core/
├── migrations/versions/0029_ledger_reversals.py
├── config/{business_event_catalog,command_catalog,tenant_isolation_catalog}.yaml
├── src/reality/
│   ├── db/core.py
│   ├── services/{core,exceptions,projections}.py
│   ├── tools/application.py
│   ├── mcp/catalog.py
│   ├── cli/app.py
│   └── web/{api,read_models}.py
└── tests/
    ├── test_ledger_reversals.py
    ├── test_ledger.py
    ├── test_master_data_api.py
    ├── test_application_tools.py
    ├── test_ai_mcp.py
    ├── test_business_events.py
    ├── test_application_catalog.py
    ├── test_migrations.py
    ├── test_materialized_projections.py
    ├── operational_exceptions/
    └── tenant_isolation/
apps/web/src/{App.tsx,api.ts,localization.tsx}
docs/{ARCHITECTURE.md,DATA_MODEL.md,WEB_SPEC.md,CLI_SPEC.md,SPEC_COVERAGE_MATRIX.md}
docs/features/ledger.md
specs/012-ledger-finance/spec.md
```

**Dependency direction**: persistence defines durable meaning; shared services own all
rules; tools and transports translate only; read models/Web explain derived results.

## Design

### Reality flow

```text
optional immutable SourceRecord → original Document Evidence
  → original immutable balanced LedgerEntry group
  → LedgerReversal (reason, actor, retry identity)
      → exact inverse immutable LedgerEntry group
  → active-allocation derivation
  → balances / open items / payments / registers / exceptions / projections
  → ledger.reversed BusinessEvent
```

`LedgerReversal` is direct durable Evidence of the correction decision and stores the
two existing opaque posting-group identities, not Document, SourceRecord, individual
Entry, or Allocation provenance. Posting group is the existing
balance/reversal aggregate even though it is represented by a shared opaque identifier
on entries rather than a separate table. Column uniqueness prevents duplicate use within
each role. Cross-role integrity is enforced by locking all tenant-owned original-group
entries before relation lookup and insertion, followed by explicit service validation;
focused concurrency tests prove this boundary. Every lookup also proves complete group
integrity. Adding and backfilling a new PostingGroup table solely to provide an FK would
expand the current ledger model without additional business behavior.

Inverse entries preserve account, party, amount, and currency, swap side, use the
accepted reversal time, and carry no copied Document/SourceRecord. LedgerReversal is
their direct correction Evidence and reaches original business Evidence. Original and
reversing groups remain visible; their sum naturally nets account/party balances to zero.

### Shared service and adapter flow

Refactor group validation/insertion into non-committing helpers while preserving the
public `post_ledger(...)` behavior. Add:

- `ledger_reversal_snapshot(...)`: tenant-safe group integrity, relation role,
  eligibility, revision, entries, allocation impact, and current derived values.
- `preview_ledger_reversal(...)`: canonical reason/request, exact inverses, affected
  allocations, and before/after values without writes.
- `reverse_ledger_posting_group(...)`: lock group entries, revalidate revision and
  fingerprint, append inverse entries/relation/event, refresh affected projections, and
  commit once.

The request fingerprint covers tenant, original opaque group ID, and trimmed reason;
actor context is audit metadata and excluded so semantically identical cross-surface
retry succeeds. Existing identical relation returns replay; divergent relation conflicts;
unique constraints are the concurrency backstop.

API exposes snapshot/preview/execute for a posting group. Web uses server preview and a
separate confirmation. CLI prints the same preview and confirms (`--yes` is explicit
automation). The mutating application tool goes through ChangeProposal and human
approval; MCP/Chat may propose but never bypass confirmation.

### Settlement and read derivation

Create one reusable active-allocation expression/helper: an allocation is operationally
active only when neither linked LedgerEntry's posting group is an original in a reversal
relation. Replace every settlement/open/payment/exception/projection calculation with
that shared semantic or its correlated SQL equivalent. Historical allocation rows remain
visible and gain derived active/inactive status plus reversal reason.

Journal and posting-group views retain both groups and derive `normal`, `reversed
original`, or `reversing` role. Account statements include both groups and naturally net.
Open items omit a reversed invoice economic effect while its former allocations become
inactive; payment views omit a reversed payment economic effect and release allocation
effects on unaffected invoices. Inspector lookup from any member returns the same chain.

### Data and migration impact

Migration `0029_ledger_reversals` adds `ledger_reversal`: opaque `id`, indexed
`tenant_id`, unique `original_posting_group_id`, unique `reversing_posting_group_id`,
required trimmed `reason`, UTC `reversed_at`, bounded serialized `actor_context`, and a
tenant-unique `request_fingerprint`. A check prevents equal role IDs. No existing entry
or allocation is changed or backfilled; absence from the relation means normal/active.

Downgrade may drop the table only while empty. Once a reversal exists, the relation is
required to interpret allocations and audit history, so downgrade refuses destructive
removal. Application rollback retains the additive table.

### Failure, security, and tenant behavior

- Select all group entries with tenant predicate and row locks; missing/foreign groups
  behave identically as not found.
- Validate nonempty, balanced, single-currency, single-party group and exact inverse set.
- Reject any group already in either role except identical retry of an original.
- Compute allocation impact from tenant-owned linked entries only.
- Stale preview or divergent/concurrent request conflicts with refresh guidance.
- Persist inverse entries and relation, then create the event and projection
  invalidations within the same transaction before its single commit; any failure rolls
  back everything.
- Emit exactly one `ledger.reversed` event with opaque group/relation IDs, reason,
  optional actor context, affected allocation IDs, and before/after financial effects.
- No Document, SourceRecord, SettlementAllocation, Movement, Reservation, Commitment,
  fulfilment, or inventory record is mutated.

## Test Strategy and Traceability

| Requirement | Test level | Planned proof | Expected initial failure |
|---|---|---|---|
| FR-001–FR-005 | migration/model/PostgreSQL story | group shapes, exact inverse, immutable original/provenance, unique relation, invalid groups | No reversal relation/service exists. |
| FR-006–FR-008 | failure/concurrency/service | rollback, identical retry, divergent race, reversal-role rejection | `post_ledger` commits directly and has no retry lock. |
| FR-009 | settlement stories | payment-side/invoice-side reversal, multi-allocation history and active state | All stored allocations currently count. |
| FR-010–FR-011 | register/business story | account/party/open/payment/journal parity; physical state unchanged | Views have no reversal roles/allocation filtering. |
| FR-012–FR-014 | API/CLI/tool/MCP/Web | mutation-free preview, stale conflict, confirmation/proposal-before-effect | No shared reversal boundary exists. |
| FR-015–FR-016 | Inspector/event/catalog | chain from either role; exact event/payload/invalidation/rollback | Event and chain are absent. |
| FR-017 | PostgreSQL isolation/catalog | two-tenant reads, writes, references, and non-disclosure | Operation is not classified. |
| DR-001–DR-005 | policy/model/review | append-only authority, shortest links, allocation history, opaque identity, adapter parity | `012/FR-008` remains a gap. |

Tests precede implementation. Run focused PostgreSQL stories, migration
upgrade/downgrade/upgrade, Ruff, full parallel backend suite, Spec policy, Web build,
EN/DE/NL/ES audit/tests, and recorded manual desktop/mobile parity before closure.

## Rollout and Rollback

Deploy the additive migration before code. Existing posting and allocation APIs remain
compatible and all old groups are normal. Monitor reversal conflicts, stale previews,
inactive-allocation counts, and event/projection failures. Code rollback retains the
table; destructive schema downgrade is allowed only when it contains no rows.

## Review Risks

- Allocation calculations are duplicated across open-item, payment, exception, and
  projection paths; missing one would create contradictory finance truth.
- Copying Document/SourceRecord to inverse entries would falsely claim direct Evidence.
- Existing posting group identity has no parent table; group-entry locking plus explicit
  cross-role, group-integrity, and tenant validation must remain one tested boundary.
- Reversing an invoice/payment with allocations changes the unaffected side; previews
  must enumerate all affected parties/documents and lock against stale settlement state.
- A reversal timestamp must not reorder or hide original economic history in explanation.
- Proposal approval and Web/CLI confirmation must revalidate exactly the previewed state.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
