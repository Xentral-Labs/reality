# Feature Specification: Faster Quality Gates

**Feature Branch**: `166-ci-quality-performance`

**Created**: 2026-09-10

**Status**: Approved

**Input**: Reduce unnecessary backend CI time and safely parallelize the PostgreSQL test suite.

**Language**: English

## Context and Intent

### Problem

The required backend quality job takes about eleven minutes and runs for every pull
request, including changes limited to the Web application. More than ten minutes are
spent in the PostgreSQL suite. The suite uses only two isolated workers even when the
host provides more capacity.

### Scope

Classify pull-request changes before scheduling backend quality, retain backend
coverage for every backend-affecting change, and split the suite across two isolated
runners with two workers each when it is required.

### Non-Goals

- Reducing test coverage or weakening required checks.
- Changing production runtime, business behavior, schema, or database services.
- Skipping the backend suite on pushes to `main`.

## User Scenarios & Testing

### User Story 1 - Fast frontend review (Priority: P1)

A contributor changing only frontend or product documentation receives CI feedback
without waiting for the unrelated PostgreSQL suite.

**Independent Test**: Classify representative changed-file lists and verify that a
Web-only list does not request backend quality while backend and workflow lists do.

**Acceptance Scenarios**:

1. **Given** a pull request changes only `apps/web` and its feature spec, **when** quality gates start, **then** backend quality is skipped successfully.
2. **Given** a pull request changes shared backend code, a backend deployment app, or backend CI policy, **when** quality gates start, **then** backend quality runs.
3. **Given** a push reaches `main`, **when** quality gates start, **then** backend quality runs regardless of its changed paths.

### User Story 2 - Faster backend validation (Priority: P2)

A contributor changing backend code receives the complete PostgreSQL result sooner,
without tests sharing a worker database.

**Independent Test**: Prove two deterministic shards cover every test file exactly
once, run both with isolated workers, and compare GitHub wall time with the 11:01 baseline.

**Acceptance Scenarios**:

1. **Given** backend quality is required, **when** pytest starts, **then** two runners execute complementary test-file shards with two database-isolated workers each.
2. **Given** tests have uneven file sizes, **when** shards are constructed, **then** a deterministic greedy allocation balances their estimated weight without omission or duplication.
3. **Given** either shard fails, **when** the required aggregate check completes, **then** `backend-quality` fails; when no backend paths changed, it succeeds with an explicit skip message.

### Edge Cases

- A quality-workflow or change-classifier edit must run backend quality to validate itself.
- An empty or unreadable pull-request diff must fail safe by requesting backend quality.
- Multiple changed scopes request every applicable quality job independently.
- Database migration and concurrency tests retain per-worker and per-test database isolation.

## Requirements

### Functional Requirements

- **FR-001**: Pull requests MUST classify whether any backend-affecting path changed before scheduling backend quality.
- **FR-002**: Backend-affecting paths MUST include the shared core, backend deployment apps, Compose definitions, dependency/lock configuration used by the backend, the classifier, and the quality workflow itself.
- **FR-003**: Unknown classifier input and pushes to `main` MUST fail safe by running backend quality.
- **FR-004**: A frontend-only pull request MUST report the existing required `backend-quality` check as successful with an explicit skip message.
- **FR-005**: A required backend suite MUST retain all test files exactly once across two runner shards, each using two xdist workers with work-stealing distribution.
- **FR-006**: Every worker MUST retain the existing unique PostgreSQL database boundary; tests that request committed databases MUST retain unique per-test databases.
- **FR-007**: The job MUST report its slowest tests to support later evidence-based optimization.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Representative frontend-only changed-file input classifies backend work as false.
- **SC-002**: Every representative backend, deployment, Compose, classifier, and workflow input classifies backend work as true.
- **SC-003**: Deterministic shard tests prove complete, non-overlapping file coverage, and both runner shards pass.
- **SC-004**: A frontend-only pull request no longer spends the prior 10:19 running PostgreSQL tests.
- **SC-005**: A backend pull-request run completes faster than the 11:01 baseline, with the exact observed duration recorded during verification.

## Requirement Traceability

- FR-001–004 → User Story 1, T001–T003, classifier unit tests and pull-request skip evidence.
- FR-005–007 → User Story 2, T004–T006, complete PostgreSQL suite and GitHub timing evidence.
- SC-001–002 → T001–T003.
- SC-003 → T005.
- SC-004–005 → T006.

## Assumptions and Dependencies

- GitHub-hosted Ubuntu runners provide at least four logical CPUs.
- pytest-xdist's worker processes continue importing `tests/conftest.py` independently,
  which creates a unique database name per worker.
- GitHub treats a conditionally skipped job as a successful required-check outcome.
- The existing GitHub Actions PostgreSQL service remains the sole CI database server.
