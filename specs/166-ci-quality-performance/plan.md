# Implementation Plan: Faster Quality Gates

**Branch**: `166-ci-quality-performance` | **Date**: 2026-09-10 | **Spec**: [spec.md](spec.md)

## Summary

Add a tested, fail-safe backend path classifier to the existing quality workflow.
Condition two backend test shards on that result for pull requests while always running
them on `main`. Each runner retains two isolated pytest workers and publishes slow-test
timings. A lightweight aggregate job preserves the required `backend-quality` check name.

## Technical Context

**Language/Version**: Python 3.12, GitHub Actions YAML

**Primary Dependencies**: Python standard library, pytest 8, pytest-xdist 3.6+, GitHub Actions

**Storage**: Ephemeral PostgreSQL 17 service; no production persistence changes

**Testing**: Python unittest for path classification; full pytest PostgreSQL suite

**Target Platform**: GitHub-hosted Ubuntu runner

**Project Type**: CI/build maintenance

**Performance Goals**: Skip approximately ten minutes for frontend-only PRs; reduce required backend wall time below the 11:01 baseline through two runner shards

**Constraints**: No test omission, main always runs, unknown paths fail safe, independent worker databases

**Scale/Scope**: One workflow, one classifier, about 2,000 backend tests

## Constitution Check

- Source/Evidence/Reality: PASS — no domain or data-flow change.
- Operational authority and schema proof: PASS — no schema or business-state change.
- Tenant/service boundaries: PASS — production code is untouched.
- Specification and test evidence: PASS — classification tests precede workflow use and the complete suite verifies parallel execution.
- Explainable Web product: PASS — no Web behavior change.
- Simplicity/storage discipline: PASS — a standard-library classifier and existing xdist dependency are reused.

Post-design re-check: PASS. No constitutional exception or complexity waiver is required.

## Project Structure

```text
.github/workflows/quality.yml
scripts/ci_backend_changes.py
scripts/test_ci_backend_changes.py
scripts/ci_backend_test_shard.py
scripts/test_ci_backend_test_shard.py
specs/166-ci-quality-performance/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/requirements.md
└── tasks.md
```

**Structure Decision**: Keep the classifier in the repository-wide scripts directory
and standard-library tests beside it in the repository-wide scripts directory. Test
files are greedily balanced by size across two runners. Do not add an Action or dependency.

## Complexity Tracking

No violations.
