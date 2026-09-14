# Implementation Plan: Always Available Storylines and Playground

**Branch**: `fix/always-available-playground` | **Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)
**Language**: English

## Summary

Delete the obsolete environment gates in shared services, retain compatible true
capability fields, remove configuration examples and exercise ordinary behavior
without fixture opt-in. No UI change is necessary.

## Technical Context

Python 3.12+, SQLAlchemy 2, PostgreSQL, FastAPI, pytest; existing React clients.
No new dependencies, infrastructure, schemas or source payload changes.
Scope: four service modules, current operator guidance/configuration and tests.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Existing setup and chapter services unchanged | PASS |
| Reality owns operational state | No business derivation or document fields changed | PASS |
| Proven schema only | No migration or schema change | PASS |
| Tenant + shared service boundaries | Remove only environment guards; keep account/owner checks | PASS |
| Spec/test traceability | Tests precede implementation; mapping below | PASS |
| Explainable web behavior | Existing API schemas and Inspector links preserved | PASS |
| Received values not recomputed | No changes to fixtures or monetary calculations | PASS |
| Smallest coherent design | Delete gates, no replacement flag or abstraction | PASS |

Both initial and post-design gates pass; no unresolved questions.

## Repository Structure and Layer Changes

Services in `packages/reality-core/src/reality/services/`:
- `storyline.py`: delete `_enabled` guard and advertise `enabled: True`.
- `playground.py`: remove start and mutation-session guards; `entry_enabled: True`.
- `company_setup.py`: always offer Sandbox after account validation; remove initializer
  gate; preserve `practice_enabled: True` for old clients.
- `free_playground.py`: delete the flag helper and refusal; keep `enabled: True`.

No domain, repository, tool, HTTP schema or frontend logic changes. Existing shared
services retain tenant scope, confirmed intent, owner locking, quotas and replay.

## Design

Existing setup still creates private Sandbox records through shared services and
normal source interpretation. Reads never seed. Completed setup still preserves
source controls; archived setup and unconfirmed actions remain refused. Availability
is product capability, not proof of individual account eligibility.

## Test Strategy and Traceability

| Requirements | Tests/evidence | Initial failure |
|---|---|---|
| FR-001–002 | `tests/test_storyline_library_api.py`, `test_playground_runs.py`, `test_company_setup.py`, `test_free_playground.py`: absent/false/true/blank/malformed parameterization | Entry reports disabled or refuses start |
| FR-003, DR-001–002 | Existing `test_storyline_runs.py`, `test_playground_api.py`, `test_playground_steps.py`, setup/demo/free entry suites without opt-in fixtures | Existing protections keep passing |
| FR-004 | `.env.example`, `compose.yml`, README, worker/feature and en/de operator docs; repository search | Current docs still advertise switch |

Run focused pytest first; full `make test` with parallel workers and local test
PostgreSQL, `make lint`, `make spec-check`, docs generation/check/build, web build
and translation gates. Existing migration tests run in the full suite. Review diff.

## Rollout and Rollback

No migration. Deploy matching backend revision through the usual release process.
Old environment values become inert; operators may remove them. Old clients retain
existing availability fields. Rollback restores previous code and opt-in semantics.
This task changes code only; production rollout is separate.

## Review Risks

Do not remove remaining independent quota controls, authentication or confirmation.
Remove stale fixture opt-ins so tests prove the normal configuration. Historical
specs retain evidence with an explicit supersession note.

## Complexity Tracking

None; no exceptions or new abstractions.
