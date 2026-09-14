# Implementation Plan: Read Capability Guidance

**Branch**: `047-read-capability-guidance` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Generalize the existing validated capability metadata into explicit `proposal` and
`read` variants. Keep proposal validation unchanged; validate read identity against
the public MCP registry and non-mutating application tools. Add six reviewed entries,
serve both variants through `capability_describe`, and document the agent loop.

## Technical Context

Python 3.12, YAML application catalog, existing tool/MCP registries, pytest, and
VitePress Docs. No storage, dependency, API execution, or Product Web changes.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Each read names its actual data basis and non-proof. |
| Reality authority | PASS | Guidance cannot promote search, projections, or exceptions. |
| Proven schema | PASS | No schema or migration. |
| Tenant/shared boundaries | PASS | Existing read-only lookup and runtime tools remain authoritative. |
| Spec/tests first | PASS | Contract and planted-defect tests precede changes. |
| Explainability | PASS | Agent-facing limitations and unknown states are explicit. |
| Simplicity | PASS | One discriminated catalog contract; no workflow or prompt system. |

Post-design check: PASS. No exceptions.

## Design

Every guidance entry has `kind`. Existing proposal entries default to `proposal`
for compatibility and retain their current normalized response. Read entries require
one public tool identity, one non-mutating application target, purpose, use/non-use,
context, data-basis references, limitations, freshness, empty/refusal behavior,
verification role (`discovery`, `context`, or `independent`), proof/non-proof,
unknown conditions, next steps, and examples.

Data-basis values resolve against controlled data-model records, projection names, or
operational concepts explicitly allowlisted by the validator. Runtime tenant access is
not evaluated by guidance. No migration or rollback data work exists.

## Paths and Tests

- `config/command_catalog.yaml`: six read entries.
- `src/reality/catalogs.py`: discriminated validation.
- `tests/test_capability_guidance.py`: read matrix and defects.
- `tests/test_agent_command_parity.py`: public/read parity.
- Docs concept and contract test: selection and verification loop.

Rollback removes read entries and validator branch; proposal behavior remains stable.

