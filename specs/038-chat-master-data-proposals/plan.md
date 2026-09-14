# Implementation Plan: Chat Master Data Proposals

**Branch**: `038-chat-master-data-proposals` | **Date**: 2026-09-02 | **Spec**: [`spec.md`](spec.md)

**Language**: English for all repository artifacts and review evidence.
**Status**: Scope approved by the product owner on 2026-09-02.

## Summary

Add three typed proposal tools for Party, Item, and Location creation to the canonical
application-tool and MCP catalogs. Each accepts a non-empty list of same-family records,
uses existing field contracts and optional SourceRecord semantics, and executes the
batch atomically through new thin shared-service batch functions. The Copilot prompt
states that these operational references may be created manually. No model or schema
changes are needed.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, Pydantic v2-compatible JSON schemas, OpenAI-compatible and Anthropic tool-call adapters
**Storage**: PostgreSQL; existing optional immutable SourceRecord provenance
**Testing**: pytest unit, service, catalog, proposal, provider-adapter, and PostgreSQL business stories
**Project Type**: backend services plus internal Copilot and external MCP adapters
**Constraints**: Opaque IDs; lossless optional source; tenant scope; no direct adapter ORM writes; explicit confirmation
**Scale/Scope**: Three create-only master-data families; same-family batches; no update/lifecycle tools and no schema change

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Master references may exist without Source; when supplied, existing immutable SourceRecord linkage is retained. Evidence and Reality stages do not apply to reference creation. | PASS |
| Reality owns operational state | Only Party, Item, and Location reference identities are created; no operational status moves to them or Documents. | PASS |
| Proven schema only | Existing entities and ChangeProposal representation are sufficient; migrations are prohibited. | PASS |
| Tenant + shared service boundaries | Copilot/MCP proposal → application tool → tenant-scoped batch service → existing creation rules; confirmation remains mandatory. | PASS |
| Spec/test traceability | Every FR/DR maps to catalog, service, proposal, confirmation, atomicity, tenancy, or prompt evidence below. | PASS |
| Explainable web behavior | Pending proposal metadata exposes family and exact arguments; existing approval UI remains authoritative. | PASS |
| Smallest coherent design | Three explicit schemas avoid unsafe generic CRUD; thin family batch services reuse existing validation/building logic. | PASS |

Planning MUST stop while any row is FAIL or unresolved.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/core.py        # atomic family batch services and shared create internals
packages/reality-core/src/reality/tools/application.py    # canonical mutating application tools
packages/reality-core/src/reality/mcp/catalog.py          # typed propose schemas and metadata
packages/reality-core/src/reality/agent/mcp_chat.py       # semantic prompt clarification
packages/reality-core/src/reality/catalogs.py             # hide private transaction controls from public service contracts
packages/reality-core/config/tenant_isolation_catalog.yaml # classify new services and tools
packages/reality-core/tests/test_chat_master_data.py      # service/proposal/confirmation/atomicity stories
packages/reality-core/tests/test_ai_mcp.py                 # catalog and MCP exposure regression
packages/reality-core/tests/test_application_catalog.py    # tenant-operation drift count
packages/reality-core/tests/test_mcp_chat.py               # provider schema/prompt behavior
docs/features/chat.md                                      # durable Chat contract
```

Dependency direction remains Copilot or MCP → canonical catalog → application tool →
shared tenant-scoped service → persistence. The agent and adapters never receive a new
persistence path.

## Design

### Reality flow

Party, Item, and Location remain operational reference identities. SourceRecord is an
optional lossless Source stage and is linked only when both source system and external
ID are supplied. Document/Evidence and operational Reality records are not created.

### Service and adapter flow

- Add family-specific batch service entry points accepting canonical dictionaries.
- Share private no-commit builders with the existing single-record services so field
  validation, event emission, optional provenance, and opaque identity generation do
  not fork.
- Validate and build every record inside one service-owned transaction and commit once.
- Resolve Location `ref`/`parent_ref` values in input order inside that transaction;
  retain `parent_location_id` exclusively for existing opaque identities.
- Register `party_create`, `item_create`, and `location_create` as canonical mutating
  application tools.
- Register corresponding `*_propose` catalog definitions with `records` arrays,
  required fields, established defaults, optional source fields, and no unknown keys.
- Existing `_propose` stores exact arguments in ChangeProposal. Existing explicit
  confirmation dispatches the family tool and records returned opaque IDs.
- Both OpenAI-compatible and Anthropic Copilot adapters derive their schemas from the
  same catalog. The prompt explains manual creation and optional provenance.
- The Proposal card opens the existing confirmation dialog with a `Review` action; only
  the dialog labels its final mutation `Approve & execute`.

### Data and migration impact

No table, column, constraint, index, migration, seed, or backfill. Existing
ChangeProposal JSON stores the typed batch arguments. Rollback removes catalog/tool
registrations and code paths; already confirmed master records remain legitimate records.

### Failure, security, and tenant behavior

Blank required values, invalid enums, incomplete source identity pairs, and foreign
relationship IDs fail the complete batch. A service rollback leaves no record,
SourceRecord, role, or business event from that attempt. Proposal creation never writes
business state. Confirmation remains separately permissioned and an executed proposal
cannot be replayed.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-005 | catalog/unit | `test_master_data_proposal_schemas_expose_required_fields_defaults_and_optional_source` | Tools are absent. |
| FR-006, FR-010 | proposal/service | `test_master_data_tools_only_create_typed_pending_proposals` | Tool names are unknown. |
| FR-007 | business story | `test_confirmed_master_data_proposals_use_shared_services` | No handlers execute master creation. |
| FR-008 | PostgreSQL service story | `test_master_data_batch_confirmation_is_atomic` | No batch service exists. |
| FR-009 | adapter/prompt | `test_copilot_prompt_declares_manual_master_data_and_optional_source` plus tool-schema assertions | Prompt can imply an import-only path. |
| DR-001–DR-003, DR-005 | structural/review | handler delegation and schema-diff review | Catalog coverage is absent. |
| DR-004 | tenant story | foreign parent/default Location batch rejection | No Chat master-data execution path exists. |

Tests are added and observed failing before production changes where practical. Focused
unit tests prove catalog/proposal behavior; PostgreSQL runs prove transaction and tenant
semantics because PostgreSQL is the supported business database.

## Rollout and Rollback

The tool catalog grows additively. Tokens with wildcard permission see the new tools;
explicit allowlists must opt in, preserving least privilege. No migration ordering is
required. Rolling code back removes creation capability without altering existing data.

## Review Risks

- Accidentally exposing confirm access to the internal Copilot instead of proposal only.
- Duplicating master-data validation in schemas or handlers rather than keeping services authoritative.
- Committing per record and leaving partial batches after a later validation failure.
- Creating synthetic SourceRecords for manual records without provenance.
- Allowing catalog defaults to drift from Web, API, CLI, or service defaults.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Post-Design Constitution Re-check

All checks remain PASS. The design adds no persistence field, alternate adapter rule, or
generic mutation abstraction.
