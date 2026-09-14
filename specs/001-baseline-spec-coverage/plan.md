# Implementation Plan: Existing-System Specification Baseline

**Branch**: `001-baseline-spec-coverage` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and recorded owner decisions.

## Summary

Create a documentation-only baseline of thirteen bounded Business Reality capability
groups. Build one coverage matrix from durable contracts, persisted concepts, public
behavior, and executable evidence; then create and owner-review one as-is feature spec
per group. Preserve uncertainty through explicit evidence statuses and decision logs.
No product behavior, schema, or runtime dependency changes are permitted.

## Technical Context

**Language/Version**: Markdown artifacts; Python 3.12 for deterministic policy checks
**Primary Dependencies**: GitHub Spec Kit 1.0.0, repository contracts, data-model catalog, pytest collection
**Storage**: Git-tracked Markdown under `specs/`; no business storage changes
**Testing**: Spec-policy checks, coverage validation, link/path validation, existing full quality gates
**Project Type**: Documentation/governance baseline for a backend and independent frontend product
**Constraints**: No observable behavior or schema change; no retroactive approval; maximum three owner questions per review batch
**Scale/Scope**: 20 feature documents, 35 backend test files, 13 capability specs, 48 catalogued business tables

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Every baseline uses DR-001 and evidence links | PASS |
| Reality owns operational state | Stored/derived classification and contradiction reporting are mandatory | PASS |
| Proven schema only | No schema change; catalog is read-only evidence | PASS |
| Tenant + shared service boundaries | DR-003 is required in every capability baseline | PASS |
| Spec/test traceability | FR/DR → source/status/test rows are required | PASS |
| Explainable web behavior | DR-005 covers operational results and Inspector traces | PASS |
| Smallest coherent design | Thirteen business groups; artifacts remain evidence, not separate specs | PASS |
| English repository language | Spec metadata and FR-013 require English artifacts | PASS |

The gate passes before research and after design: outputs are documentation or
validation artifacts and introduce no constitutional exception.

## Repository Structure and Layer Changes

```text
specs/001-baseline-spec-coverage/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/coverage-matrix.md
├── checklists/requirements.md
└── tasks.md

specs/003-.../ through specs/016-.../ (excluding independent change spec 007)
└── spec.md + checklists/requirements.md per baseline capability

docs/SPEC_COVERAGE_MATRIX.md
scripts/check_spec_policy.py
```

**Files/layers affected**: Specification, documentation, and optional policy-check
files only. `backend/src/`, `backend/migrations/`, and `frontend/src/` are read-only
evidence sources and must have no baseline-generated diff.

## Design

### Reality flow

Each capability spec names its Source, Evidence, and Reality stages and the shortest
authoritative relationships. A stage may be absent only with a bounded business
explanation. Requirements explicitly separate stored records from derived views.

### Evidence and review flow

For each capability group:

1. Read its primary feature contracts and cross-cutting authorities.
2. Inventory related catalog tables, services/tools, adapters, and tests.
3. Draft requirements without treating implementation as intent.
4. Assign one evidence status and source set per requirement.
5. Record contradictions and at most three material questions.
6. Obtain owner answers and update the spec/checklist.
7. Mark the baseline `Reviewed` only after ambiguity is closed; evidence gaps remain
   visibly non-verified and become later change work.

Review batches follow dependency order: foundation; Source/Evidence; operational
Reality; O2C/P2P/finance; explanation/interaction/demo; Web product surface.

### Data and migration impact

No database model, migration, fixture, or generated product catalog changes are
allowed. `data-model.md` describes documentation records only. A missing or questionable
typed field is recorded as a gap and requires a future change spec.

### Failure, security, and tenant behavior

- Missing evidence prevents `Verified as-is`; it never aborts the whole baseline.
- A constitutional contradiction blocks review of the affected requirement.
- Tenant/security behavior receives dedicated DR coverage where applicable.
- Secrets and local `.env` content are never specification evidence.
- Generated assets, caches, and dependencies are excluded from coverage.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-002 | coverage audit | All source categories map to one owner | Matrix/specs initially missing |
| FR-003–FR-010 | spec validation | Sections, statuses, evidence links | Baseline specs initially absent |
| FR-011, FR-013 | completeness audit | Thirteen English capability specs present | Only meta-spec exists initially |
| FR-012 | diff audit | No baseline change under product paths | Pass unless accidental edit occurs |
| DR-001–DR-005 | checklist review | Domain checklist per baseline | Checklists initially absent |

Existing Ruff, PostgreSQL pytest, frontend build, and i18n audit remain regression gates.

## Rollout and Rollback

Land the meta-spec, plan, and tooling in the Spec-Kit foundation PR. Generate baseline
specs in small reviewable batches. Rollback is documentation reversion; no data or
runtime rollback exists. A baseline becomes the default discovery authority only after
its owner-review state is `Reviewed`.

## Review Risks

- Confusing green tests with desired business intent.
- Duplicating cross-cutting invariants until copies drift.
- Creating specs too fine-grained or too broad.
- Hiding future intent inside as-is requirements.
- Missing behavior implemented only in adapters or UI.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Post-Design Constitution Re-check

All seven principles remain PASS. There is no new business field, relationship,
persistence path, adapter rule, or unreviewed implementation authorization.
