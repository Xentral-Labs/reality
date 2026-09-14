# Tasks: Always Available Storylines and Playground

## Phase 1: Setup and foundation

- [x] T001 Record approved scope and quality review in `specs/193-always-available-playground/spec.md` and `checklists/requirements.md`.
- [x] T002 Record design, compatibility and Constitution Check in `specs/193-always-available-playground/plan.md` and supporting artifacts.

## Phase 2: US1 — Regular practice entry

Independent test: every supported entry succeeds for an eligible account with
absent/false/true/empty/malformed retired flag values.

- [x] T003 [US1] Add failing parameterized service/API proofs to `packages/reality-core/tests/test_storyline_library_api.py`, `test_playground_runs.py`, `test_company_setup.py`, `test_free_playground.py` (FR-001–002).
- [x] T004 [US1] Remove flag guards and preserve compatible true capability fields in `packages/reality-core/src/reality/services/storyline.py`, `playground.py`, `company_setup.py`, `free_playground.py` (FR-001–002).

## Phase 3: US2 — Existing boundaries

Independent test: admission, ownership, confirmations, quotas, archived companies,
source controls and replay keep their existing outcomes without flag fixture setup.

- [x] T005 [US2] Remove obsolete opt-in fixture lines; replace switch-refusal assertions with regular entry/confirmation/quota checks in `packages/reality-core/tests/test_storyline_runs.py`, `test_playground_runs.py`, `test_playground_api.py`, `test_playground_steps.py` and related demo/setup tests (FR-003, DR-001–002).
- [x] T006 [US2] Run focused service/API/story tests and full backend suite; record evidence in `specs/193-always-available-playground/verification.md` (FR-001–003, DR-001–002).

## Phase 4: Documentation and review

- [x] T007 Remove current switch guidance from `.env.example`, `compose.yml`, `README.md`, `docs/WORKER_DEPLOYMENT.md`, `docs/features/company-setup-demo.md`, `docs/features/learning-playground.md` and `apps/docs/content/{operations,reference,de/operations,de/reference}`; cross-reference superseded specs (FR-004).
- [x] T008 Run lint, specification, docs/catalog and web gates; review diff and record results in `specs/193-always-available-playground/verification.md` (all requirements).

## Dependencies and implementation strategy

T001 → T002 → analysis → T003 → T004 → T005 → T006 → T007 → T008.
T003 also updates obsolete expected refusals before service edits so meaningful
red tests are visible. US1 is the smallest delivery; US2 is required before done.
Independent docs review can run alongside verification, but no agents are needed.
