# Implementation Plan: Business-readable Inspectors

**Branch**: `073-business-readable-inspectors` | **Date**: 2026-09-04 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Extend the existing tenant-scoped inspector read model with explicit business summary,
reference, meaning, and guidance fields, starting with Facts and operational Exceptions.
Render every supported record through one reordered shared drawer: business summary and
current position first, explanation chain and related context second, exact identifiers,
events, and source payload in a collapsed technical section. No stored data or business
rule changes.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/React frontend
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI, React/Vite
**Storage**: Existing PostgreSQL reads only; no schema change
**Testing**: pytest API/business stories; Node frontend contracts; frontend build and i18n audit
**Project Type**: backend service/API plus independent frontend
**Constraints**: UTC; opaque IDs; lossless source; strict tenant scope; business copy produced server-side
**Scale/Scope**: One bounded record per inspector request and existing bounded related rows/events

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The existing inspector trail is relabelled and preserved in exact order; raw SourceRecord remains available. | PASS |
| Reality owns operational state | The change presents existing Facts and Reality reads and adds no Document state. | PASS |
| Proven schema only | No schema, migration, or copied display field is introduced. | PASS |
| Tenant + shared service boundaries | Existing tenant-scoped inspector builders produce all business context; the browser only renders it. | PASS |
| Spec/test traceability | FR/DR requirements map to API stories, UI contracts, build, and visual evidence. | PASS |
| Explainable web behavior | The first viewport answers meaning, position, reason, action, and trace in the required order. | PASS |
| Smallest coherent design | One read-contract extension and one shared drawer replace per-register redesigns. | PASS |

Planning may proceed. No Constitution exception is requested.

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/web/api.py        # tenant-scoped inspector presentation reads
packages/reality-core/tests/test_master_data_api.py # Fact/Exception inspector stories
apps/web/src/api.ts                                 # typed read contract
apps/web/src/App.tsx                                # one shared business-first inspector
apps/web/src/styles.css                             # shared responsive hierarchy
apps/web/src/localization.tsx                       # complete four-language copy
apps/web/scripts/ux-operational-contract.test.mjs  # hierarchy and disclosure contract
docs/WEB_SPEC.md                                    # durable inspector behavior
```

Dependency direction remains Web → HTTP adapter → tenant-scoped service/domain reads.
No browser-owned business calculation is added.

## Design

### Reality flow

The server follows existing direct relationships for the requested record. A Fact may
follow Fact → subject and Fact → SourceRecord, then the subject's existing Evidence link
when present. An Exception follows its derived record and trace. Human references are
returned only as display context; opaque IDs remain identity.

### Service and adapter flow

The existing `/inspector/{kind}/{record_id}` endpoint returns a common presentation
contract. Add business meaning, reference, and guidance values to that contract. Fact
and Exception builders enrich those values through tenant-scoped reads. Other builders
provide conservative summaries from fields they already load. The shared React drawer
renders the values without class-specific business branching.

### Data and migration impact

No schema or migration. All added values are transient read-model fields derived from
existing tenant-scoped records. Rollback removes those response fields and restores the
prior drawer layout.

### Failure, security, and tenant behavior

Existing not-found behavior and tenant filters remain unchanged. Missing optional
context yields honest fallback copy. Loading a new target clears prior data before the
request, so stale record context cannot remain visible. The feature is read-only and
requires no confirmation path.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-002-FR-007; DR-001-DR-004 | API business story | Fact and same-titled Exception inspector assertions in `test_master_data_api.py` | Response lacks explicit summary/reference/guidance contract. |
| FR-001; FR-005-FR-009 | Frontend contract | Shared hierarchy and collapsed technical-detail assertions | Drawer currently leads with state/ID and exposes activity outside technical detail. |
| FR-008; SC-004 | Responsive contract/visual | CSS narrow-layout contract plus 390 px review | New hierarchy has no defined responsive acceptance yet. |
| DR-005 | Review/spec gate | Migration and diff review | Any schema change fails the planned review. |

## Rollout and Rollback

The API fields are additive and the Web deploy consumes them. Existing record links and
the inspector endpoint remain stable. Rollback is a code-only revert with no data work.

## Review Risks

- A generic summary can become vague; Fact and Exception acceptance stories require
  record-specific server copy.
- Business references must never become identity or bypass tenant scope.
- Hiding technical data must not remove traceability; all current exact fields remain
  inside an explicit disclosure.
- Long explanations and false/zero Fact values must remain visible and correctly worded.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
