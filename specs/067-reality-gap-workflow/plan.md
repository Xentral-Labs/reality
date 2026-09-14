# Implementation Plan: Reality Gap Workflow

**Branch**: `067-reality-gap-workflow` | **Date**: 2026-09-04 | **Spec**: [spec.md](spec.md)

## Summary

Add a tenant-scoped Reality Gap workflow shared by Chat, MCP, and Web. It stores questions, guided investigation, evidence references, classification, and implementation receipts. Owners may activate a closed ERP-ready declarative `SourceRecord → Fact` rule with bounded ALL/ANY condition groups, extracted or constant output, Commitment or DocumentLine resolution, bounded line iteration, effective time, conflict visibility, and resumable replay after simulation; other classifications produce a developer handoff without runtime changes.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, React/Vite
**Storage**: PostgreSQL plus existing immutable SourceRecord storage
**Testing**: pytest service/story/adapter/migration; frontend build, focused UI tests, i18n audit
**Project Type**: backend services/API/MCP plus independent frontend
**Constraints**: UTC, opaque IDs, strict tenant scope, immutable sources/Facts, no executable user expressions, confirmation for mutating agent calls
**Scale/Scope**: 10,000 gaps and 100,000 entries per tenant; 25-row queue pages; 20 rule conditions; 500 elements per source; 100-source simulations; 500-source deterministic replay pages

## Constitution Check _(blocking gate)_

| Principle                          | Evidence in this plan                                                                                               | Result |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------ |
| Source → Evidence → Reality        | Rules retain SourceRecord and Fact links; subject resolution follows existing SourceRecord → Document → Commitment. | PASS   |
| Reality owns operational state     | Rules create contextual Facts only and add no Document operational state.                                           | PASS   |
| Proven schema only                 | New storage exists only for approved capture, audit, activation, and replay stories.                                | PASS   |
| Tenant + shared service boundaries | Every lookup/evaluation is tenant-scoped; Chat/MCP/Web call shared application operations.                          | PASS   |
| Spec/test traceability             | FR/DR map to service, rule, tenant, proposal, HTTP, MCP, Chat, UI, migration, and benchmark tests.                  | PASS   |
| Explainable web behavior           | Detail exposes question → evidence → recommendation → decision → rule/result → source.                              | PASS   |
| Smallest coherent design           | V1 uses closed operators/resolvers, bounded ALL/ANY groups, one array boundary, and no general expression language. | PASS   |

Planning may proceed. No Constitution exception is requested.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/db/core.py
packages/reality-core/src/reality/services/reality_gaps.py
packages/reality-core/src/reality/services/core.py
packages/reality-core/src/reality/tools/application.py
packages/reality-core/src/reality/mcp/catalog.py
packages/reality-core/src/reality/web/api.py
packages/reality-core/migrations/versions/0035_reality_gaps.py
packages/reality-core/migrations/versions/0036_erp_interpretation_rules.py
packages/reality-core/tests/test_reality_gaps.py
packages/reality-core/tests/test_reality_gap_rules.py
packages/reality-core/tests/test_reality_gap_tools.py
apps/web/src/api.ts
apps/web/src/App.tsx
apps/web/src/localization.tsx
docs/features/reality_gaps.md
docs/WEB_SPEC.md
docs/WEB_UX_MATRIX.md
```

Dependency direction: Chat/MCP/Web → application tool/service → gap service → gap/rule/outcome persistence. Source ingestion → shared evaluator → canonical Fact primitive. Adapters never write ORM state.

## Design

### Reality flow

```text
SourceRecord ─→ RealityGap ─→ InterpretationRuleVersion
     │                                  │
     └→ Document ─→ Commitment ←target──┘
     └──── evaluated by active rule ─→ Fact ←─ InterpretationOutcome
```

RealityGap is modeling workflow, never operational truth. Developer packages cannot execute. Rule-produced Facts retain exact rule-version provenance.

### Service and adapter flow

- Read operations list/detail gaps, guided questions, simulation, and results.
- Mutations capture, append, recommend, decide, prepare, activate, disable, and replay through registered tools. Chat/MCP expose proposal-only mutations; Web uses the same handlers with owner checks.
- Web adds **Open questions** under Data Management and contextual entry points from Facts/source inspection.
- Web keeps Open questions as the durable queue and detail workspace. A single call to action opens Ask Reality with a prefilled business-language capture request; Chat performs the guided capture through the shared tools.
- Gap detail calls a bounded tenant-scoped source-example search service. It exposes safe scalar payload candidates and attaches the selected SourceRecord ID, field path, and displayed value through the existing evidence-entry mutation; the browser implements no matching or provenance rules.
- Typed tools are authoritative; deterministic Chat recognizes explicit capture intent while configured providers can guide the complete workflow through those tools.

### Declarative rule boundary

V1 permits exact `source_system`/`source_type`, restricted dot/index JSON paths, at most 20 comparisons in three levels of explicit ALL/ANY groups from a closed operator registry, explicit path or constant output, one bounded array iteration, tenant-local predicates, Commitment and DocumentLine resolvers, scalar value contracts, finite enum mapping, trim/lowercase normalization, and received-time or timezone-aware restricted-path observation time. It permits no code, SQL, regex, templates, network calls, wildcards, recursive descent, functions, arithmetic, or arbitrary expressions. Simulation, ingestion, and replay use one evaluator; ambiguity and conflicts fail closed.

Conditions and rule configuration remain canonical immutable JSON on the versioned rule because they have no independent business identity. Interpretation outcomes gain a nullable source element index and deterministic uniqueness per rule/source/element. Existing rows are upgraded to explicit path output without changing their meaning.

### Data and migration impact

Add the four tenant-scoped tables in [data-model.md](data-model.md) and nullable `interpretation_rule_id` on Fact in migration 0035. Migration 0036 adds versioned condition/output/iteration fields and per-element outcome identity, backfills existing rules to explicit source-path output, and adds summary/replay indexes. No Source, Evidence, or Reality row is rewritten. Routine rollback disables rules; the 0036 downgrade removes only the new configuration after verifying no rule depends on it.

### Failure, security, and tenant behavior

- Foreign context behaves as not found; revisions reject stale changes.
- Rule versions become immutable after draft; only active owners classify or control rules.
- Members capture, answer, inspect, and simulate.
- Activation is atomic. Replay uses deterministic Fact identity and durable per-source outcomes.
- Rule failure never rolls back immutable source receipt or blocks unrelated interpretation.
- Condition misses are durable normal outcomes; invalid values, ambiguous subjects, and conflicts remain separate inspectable failures.
- Replay cursors are opaque validated tokens bound to tenant, exact rule ID, and requested scope; they carry no authority, and deterministic keyset pagination avoids offset drift.
- Competing rule families receive no implicit priority. Newly detected conflicts create no Fact and remain visible for owner review.

## Test Strategy and Traceability

| Requirement                           | Test level             | Planned test                                                                                     | Expected initial failure                                                   |
| ------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| FR-001–FR-007, FR-014–FR-016          | service/story          | gap capture, revision, context, queue, history, tenant tests                                     | Entities/service absent                                                    |
| FR-008–FR-011, FR-017–FR-020, FR-027  | service/story          | recommendation, classification, package, settlement                                              | Lifecycle absent                                                           |
| FR-021–FR-026, DR-005, DR-009–DR-010  | unit/service           | evaluator, simulation, activation, ingestion, replay                                             | Rule evaluator absent                                                      |
| FR-009, FR-012–FR-013, DR-004         | tool/MCP/Chat          | proposal-only mutation, approval, stale, schemas, parity                                         | Tools absent                                                               |
| FR-001, FR-005, FR-010, FR-019–FR-023 | HTTP/UI                | member/owner routes, page/build/i18n                                                             | Routes/UI absent                                                           |
| DR-001–DR-003, DR-007–DR-008          | migration/inspection   | constraints, downgrade, trace, immutability                                                      | Schema absent                                                              |
| SC-007                                | benchmark              | 10k/100k bounded queue PostgreSQL benchmark                                                      | Index/query absent                                                         |
| FR-028, SC-008                        | Web contract/usability | guided capture structure, examples, progress, back navigation, and outcome explanation           | Existing blank two-field form creates hesitation                           |
| FR-031                                | service/HTTP/UI        | bounded tenant source search, safe candidate extraction, source-linked evidence, manual fallback | No in-context source finder exists                                         |
| FR-038                                | Web contract/usability | actionable queue, completed table, and explicit overview/detail navigation                       | Terminal work currently looks actionable and detail navigation is implicit |
| FR-039                                | service/HTTP/UI        | tenant-scoped lifecycle counts, search, status filtering, and bounded register pages             | Client-only filtering would become incomplete after the first bounded page |
| FR-040–FR-045, DR-011–DR-012          | unit/service/migration | operator/type matrix, output modes, skips, line iteration/resolution, effective time, upgrade     | Existing evaluator treats every valid scalar as applicable                  |
| FR-046–FR-055, DR-013                 | service/tool/HTTP/UI   | conflicts, immutable revisions, replay cursor/resume, summaries, authorization, surface parity    | Current fixed replay and hidden outcomes are insufficient                   |

## Rollout and Rollback

Apply additive schema with no active rules; deploy capture before activation. Existing sources remain unchanged until confirmed replay. Rollback disables active rules and deploys without evaluation; immutable historical Facts remain.

## Review Risks

- Path evaluation accidentally becoming an expression language.
- Wrong subject attachment; ambiguity must fail closed.
- Tenant predicates bypassing global contracts.
- Existing Fact commit boundary must be split for coherent ingestion.
- Raw examples may contain personal data.
- Comparison coercion could make semantically different ERP values appear equal.
- Line/source coordinates may not match an imported DocumentLine and must fail closed.
- Replay cursor scope or ordering bugs could skip or duplicate historical evaluation.
- Multiple rule families could generate contradictory current observations without visible conflict handling.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
| ---------------------- | ---------- | ---------------------------- | -------- |
| None                   | —          | —                            | —        |

Post-design re-evaluation: all rows remain PASS.
