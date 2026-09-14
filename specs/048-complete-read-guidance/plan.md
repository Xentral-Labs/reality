# Implementation Plan: Complete Read Capability Guidance

**Branch**: `048-complete-read-guidance` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

## Summary

Complete the validated read-guidance registry for the six remaining public business
reads, enforce registry completeness, and move pending-proposal listing behind the
existing application read dispatcher. No domain state or read result changes.

## Technical Context

Python 3.12, YAML application catalog, MCP/application tool registries, pytest, and
VitePress documentation. No storage, dependency, schema, API shape, or UI changes.

## Constitution Check

| Principle                   | Result | Evidence                                                          |
| --------------------------- | ------ | ----------------------------------------------------------------- |
| Source → Evidence → Reality | PASS   | Descriptions name actual Reality/projection bases and non-proofs. |
| Reality authority           | PASS   | Queues, exceptions, proposals, and balances remain derived.       |
| Proven schema               | PASS   | No schema or migration.                                           |
| Tenant/shared boundaries    | PASS   | Pending proposals moves to the shared read dispatcher.            |
| Spec/tests first            | PASS   | Completeness and semantic tests precede catalog changes.          |
| Explainability              | PASS   | Every read states proof, non-proof, and unknown conditions.       |
| Simplicity                  | PASS   | Extends the existing discriminated catalog only.                  |

Post-design check: PASS. No exceptions.

## Design

Derive the required guidance identities from public MCP entries with access `read`,
excluding only `capability_describe`. Validate that this derived set is present in the
guidance catalog. Each entry continues to resolve to an existing non-mutating
application tool. Add a thin pending-proposal application read wrapper and route MCP
through `_read` so Chat and MCP share the same boundary.

## Paths, Tests, and Rollback

- Catalog and validator: `packages/reality-core/config/command_catalog.yaml`,
  `packages/reality-core/src/reality/catalogs.py`.
- Shared routing: `packages/reality-core/src/reality/tools/application.py`,
  `packages/reality-core/src/reality/mcp/catalog.py`.
- Proof: capability guidance, parity, and MCP tests.
- Public documentation and contract tests describe the complete read set.

Rollback removes six entries and completeness enforcement and restores the direct MCP
pending-proposal adapter. No data rollback exists.
