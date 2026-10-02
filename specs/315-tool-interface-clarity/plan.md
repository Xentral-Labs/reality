# Implementation Plan: Tool interface clarity

**Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)
**Language**: English

## Summary

Publish one localized interface guide from the catalog generator to both Vue and Markdown. Label workspace actions Web actions, add an actual reservation example, and explicitly group operation relationships. Record the three-operation audit; consolidate the proven category-copy duplication only.

## Technical Context

Python 3.12+ catalog generator, Vue/TypeScript VitePress documentation, existing JSON metadata. No storage, dependencies, MCP runtime or business service changes. Node documentation contract tests and Python reference tests plus documentation build provide the required checks.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Catalog presentation only; no record writes | PASS |
| Reality owns operational state | No state/schema changes | PASS |
| Proven schema only | No database changes | PASS |
| Tenant + shared service boundaries | Existing handlers/services untouched | PASS |
| Spec/test traceability | FR/DR mapped below; regression proof precedes implementation | PASS |
| Explainable web behavior | Real command relationships and proposal confirmation explained | PASS |
| Received values not recomputed | No business values processed | PASS |
| Smallest coherent design | Reuse generator/model; reject universal schema/form generation | PASS |

## Repository Structure and Layer Changes

- `apps/docs/scripts/generate-catalog-reference.py`: canonical guide metadata and manual rendering.
- `apps/docs/.vitepress/theme/components/ToolUsage.vue`: consume guide and existing links.
- `apps/docs/scripts/docs-contract.test.mjs`: generated-data and UI integration assertions.
- `apps/docs/scripts/test_interface_guide_reference.py`: renderer/catalog relationship proof.
- `apps/docs/scripts/tool-interface-render.test.mjs`: actual Vue rendering for both languages and mapped/unmapped entries.
- Generated `apps/docs/content/{,de/}tool-usage/` and `.vitepress/data/tool-usage.json`.
- Feature artifacts document audit and verification.

## Design

### Reality and service flow

No domain/service/tool behavior changes. Audit shows Web/action and agent proposal paths reuse application services. The reservation explanation includes preparation, explicit approval and execution rather than suggesting immediate mutation.

### Presentation flow

Generator guide → generated JSON → Vue labels/overview; the same guide → manual tables and example links. Resolve reservation action, command and proposal tool through existing catalogs, fail on inconsistent example references. Derive operation relationship groups from existing entry links, avoiding a new hand-maintained mapping. Keep general business-resource Actions wording.

### Data, migration, failure and security

No migrations or mutations. Preserve technical keys/anchors and public MCP schema. Existing loading/error behavior remains; render the guide only after model load. Category counts retain their current computation. Existing unmapped tools remain discoverable and described.

## Test Strategy and Traceability

| Requirement | Proof | Initial failure |
|---|---|---|
| FR-001, FR-002 | Node contract and Python renderer guide tests | Missing guide and Web label |
| FR-003 | Python/Node catalog-resolved example tests | Missing example metadata |
| FR-004 | Node relationship/UI integration checks | No explicit relationship section |
| FR-005 | Python shared-definition and Node consumer checks | Independent copy remains |
| FR-006 | `research.md` audit and final review | Documentation review, no speculative runtime tests |
| DR-001 | Existing MCP reference/schema tests, identifier comparison and diff review | Compatibility proof; no intended failure |

## Rollout and Rollback

Deploy documentation normally. Revert documentation changes and regenerate to roll back. No client migration. Run all documentation tests/build/format, spec gate and core lint; broader PostgreSQL/backend and operational frontend suites are not required because no executable business path changes.

## Review Risks

Do not equate optional schemas with required service fields, imply proposals execute immediately, count all Web buttons, or rename general resource actions. Keep the guide compact and keyboard-accessible using existing buttons and native disclosure.

## Complexity Tracking

No Constitution exceptions. Post-design check: all rows PASS. Product scope is the already-approved session plan.
