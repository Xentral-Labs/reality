# Implementation Plan: Authoritative Price Quote Read

## Constitution Check

PASS. This exposes an existing typed Reality calculation, uses opaque tenant-scoped IDs, calls the
same application/service path as other adapters, performs no mutation, and adds no authority or
schema.

## Technical Approach

1. Extend `PriceResult` only with selection provenance already used during canonical resolution.
2. Add an application read handler that serializes the canonical result and makes no-match explicit.
3. Bind one MCP read tool with a closed input schema.
4. Register the read in executable catalogs, regenerate docs, and cover priority and isolation.

## Test Strategy

- Service/application/MCP parity tests for direct, group and default selection.
- No-match and foreign-ID refusal tests.
- Existing pricing and MCP contract regression suites.
- Spec policy, catalog generation and Ruff.
