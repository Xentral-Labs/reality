# Implementation Plan

## Technical Context
Existing Python 3.12, PyYAML, Decimal, SQLAlchemy/PostgreSQL and pytest. Local
`scenarios/` modules are developer tooling, not packaged runtime commands.
No new dependency or mutation catalog entry.

## Architecture
Fixture → controller → simulator adapter → existing company/application services.
Separate observer reads tenant-scoped authoritative records and normal quantity
services. Its expected inputs are never generated from observed Reality balances.
Store local artifacts independently of business records. Source → order evidence →
line → commitment → reservation/movement uses normal production boundaries.
Use explicit human confirmation for the fixed fixture; no agent mandate is inferred.

## Constitution Check

| Principle | Result | Reason |
| --- | --- | --- |
| Source / Evidence / Reality | PASS | Manual order services preserve lineage |
| Operational authority | PASS | No document status shortcut |
| Proven schema | PASS | No schema changes |
| Tenant / service boundary | PASS | Existing setup/proposal services; scoped reads |
| Spec / tests | PASS | Owner-approved scope; tests written before implementation |
| Explainable web | PASS | No web changes |
| Simplicity / storage | PASS | PostgreSQL only; existing dependencies |
| Received values | PASS | Fixture explicitly states line/order amounts |

## Paths and sequence
1. `scenarios/reference_week/scenario.yaml`: day/week events and checkpoint oracle.
2. `tests/scenarios/test_reference_week.py`: acceptance and failure tests first.
3. `scenarios/reference_week/simulator.py`: supported local human proposal adapter.
4. `scenarios/harness/observer.py`: scoped snapshot and exact comparison.
5. `scenarios/harness/runner.py`, `reporting.py`: barriers and standalone invocation.
6. READMEs, scenario protocol and ignored `artifacts/reference_week/` outputs.

## Rollback and risk
Remove developer modules/fixtures to roll back; no migration. Keep failed companies
for diagnosis. Never attach to a supplied existing company or retry an unknown
mutation. Trusted local actor selection is not remote authentication. Freshness is
synchronous authoritative reads, not proof of async materialized projections.

## Validation
Observe a missing-runner test failure, then day/week integration and injected-error
checks on isolated PostgreSQL. Run Ruff, spec policy and relevant existing scenario,
company and proposal tests; full backend suite as completion evidence. No frontend,
migration or generated catalog changes, so those gates are not applicable.
