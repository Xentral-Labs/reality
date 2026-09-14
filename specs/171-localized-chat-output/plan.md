# Implementation Plan: Localized Chat Output

## Summary

Pass validated profile presentation values from the authenticated HTTP boundary through the existing
chat service to both provider adapters. Add one shared system instruction; never rewrite Markdown.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Tool reads and evidence are unchanged. | PASS |
| Reality authority and received values | Presentation only; no recomputation. | PASS |
| Schema and shortest links | No schema or relationship change. | PASS |
| Tenant and service boundaries | Existing chat service and registered tools remain authoritative. | PASS |
| Tests before completion | Provider, service, and authenticated HTTP regressions are included. | PASS |
| Smallest coherent design | Reuses validated profile fields and shared provider prompt. | PASS |

## Data, Rollout, and Rollback

No migration or stored shape changes. Historical messages remain unchanged. Rollout and rollback are
code-only. Defaults preserve existing internal callers without an authenticated HTTP profile.

## Test Strategy

Run focused provider/service/HTTP tests, full backend tests, `make spec-check`, `make lint`, and the
web formatting, localization, contract, and production-build gates.
