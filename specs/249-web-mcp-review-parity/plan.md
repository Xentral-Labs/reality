# Implementation Plan: Web and MCP Proposal Review Parity

**Branch**: `249-web-mcp-review-parity` | **Date**: 2026-09-22 | **Spec**: [spec.md](./spec.md)

## Summary

Add one tenant-scoped proposal-review service that classifies every stored production proposal,
delegates to existing specialized review services, and supplies a safe common descriptor for the
remainder. Chat and Decisions route from that server classification instead of duplicate browser
lists. A common Web card confirms the exact stored proposal through the existing approval service.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI, React/Vite
**Storage**: Existing PostgreSQL ChangeProposal records; no schema change
**Testing**: pytest service/API/tenant contracts; Node Web contracts; browser acceptance
**Project Type**: shared service and thin API/Web adapters
**Constraints**: opaque IDs, UTC, tenant scope, explicit confirmation, no browser business rules
**Scale/Scope**: all current and future proposal-producing MCP definitions; one proposal at a time

## Constitution Check _(blocking gate)_

| Principle                          | Evidence in this plan                                                            | Result |
| ---------------------------------- | -------------------------------------------------------------------------------- | ------ |
| Source → Evidence → Reality        | Review retains existing source/evidence links and executes the original tool     | PASS   |
| Reality owns operational state     | No document status or parallel operational state is added                        | PASS   |
| Proven schema only                 | Descriptor is a read-time projection; no schema change                           | PASS   |
| Tenant + shared service boundaries | One scoped service supplies Web; approval uses the existing application boundary | PASS   |
| Spec/test traceability             | FR-001–FR-012 map to service, API, Web and browser tasks                         | PASS   |
| Explainable web behavior           | Every proposal exposes origin, input, preview, consequence and receipt           | PASS   |
| Received values not recomputed     | Stored input/preview/receipt are presented, not recalculated                     | PASS   |
| Smallest coherent design           | Existing specialized cards remain; one fallback replaces duplicated allowlists   | PASS   |

Planning may proceed. No exception or unresolved clarification exists.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/proposal_reviews.py
packages/reality-core/src/reality/web/api.py
packages/reality-core/tests/test_proposal_review_parity.py
apps/web/src/api.ts
apps/web/src/unified/ProposalReviewCard.tsx
apps/web/src/unified/proposalRouting.ts
apps/web/src/unified/ChatPage.tsx
apps/web/src/unified/DecisionsPage.tsx
apps/web/src/unified/UnifiedApp.tsx
apps/web/scripts/proposal-review-parity.test.mjs
docs/WEB_SPEC.md
docs/features/company-setup-demo.md
```

No domain, database, CLI or MCP execution behavior changes. The service depends on existing
proposal and specialized-review services; adapters depend on the new service.

## Design

### Reality flow

The flow stays MCP application binding → stored ChangeProposal → human review → existing
application tool → existing Source/Evidence/Reality records → stored receipt. The review descriptor
is derived at read time and is not business authority.

### Service and adapter flow

1. `proposal_reviews` loads one tenant-scoped proposal and returns review kind, destination,
   human label, safe stated input, persisted preview/status/receipt and approval requirements.
2. Conditional specialized classes are resolved on the server: reference data, item import,
   analytics report and state-bound delivery/finance actions. Existing cards remain authoritative.
3. Every other registered production tool receives `common`; sensitive values are redacted server-side.
4. Proposal lists include routing metadata. Chat and Decisions use one client route helper.
5. The common card calls existing approval/rejection endpoints and never reconstructs tool input.
6. A Python contract walks all MCP propose definitions and proves one classification plus label.
   A Web contract proves every server kind has a route/card and forbids local tool allowlists.

### Data and migration impact

No migration or backfill. Historical pending proposals use their stored input/output. Unknown
retired tools may be rejected but never confirmed through the common review.

### Failure, security, and tenant behavior

- Cross-tenant proposal IDs behave as not found.
- Sensitive keys and schema-marked sensitive values are recursively redacted by the server.
- Empty/malformed proposals show validation failure and cannot confirm; rejection remains available.
- Authorization and tool validation run during approval; stale state produces a useful refusal.
- Duplicate confirmation restores the stored status/receipt and never executes twice.
- Specialized review failure never falls back silently to the weaker common card.

## Test Strategy and Traceability

| Requirement           | Test level            | Planned test                                          | Expected initial failure                   |
| --------------------- | --------------------- | ----------------------------------------------------- | ------------------------------------------ |
| FR-001–FR-002, FR-010 | registry/Web contract | enumerate all MCP bindings and Web kinds              | most bindings lack recoverable Web routing |
| FR-003–FR-004         | service/API           | descriptor labels, nested input and redaction         | no common descriptor exists                |
| FR-005–FR-009         | service/API/story     | approve, reject, stale, replay, tenant and delegation | unsupported proposals cannot open in Web   |
| FR-011                | Web/browser           | keyboard, narrow layout, nested data and locales      | no common card exists                      |
| FR-012                | docs contract         | production-tool parity wording                        | invariant is not documented                |

Tests precede implementation. Final gates include focused backend tests, Web contracts, build,
localization audit, spec check and live MCP → Web runs for lot creation, payment terms, pricing,
finance/cost and one specialized shipment action.

## Rollout and Rollback

No data migration. Deploy API and Web together. Rollback is a code revert; all proposal and business
history remains. Older clients continue to list proposals but retain their prior review limitations.

## Review Risks

- A common card must not downgrade a stronger specialized review.
- Arbitrary source payloads may contain secrets and require server redaction.
- Confirmation must execute stored input, never browser-returned input.
- Registry imports must avoid an MCP/Web dependency cycle.
- Coverage means reloadable decision and receipt, not merely a listed proposal.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
| ---------------------- | ---------- | ---------------------------- | -------- |
| None                   | —          | —                            | —        |
