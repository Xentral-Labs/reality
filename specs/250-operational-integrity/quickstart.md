# Quickstart: Operational Integrity Verification

## Prerequisites

- PostgreSQL test service is available.
- Backend/frontend dependencies are installed.
- Tests use an isolated database.

## Focused verification

Add tests first and observe meaningful failures on the prior behavior, then run:

```bash
pytest -q \
  packages/reality-core/tests/test_returns.py \
  packages/reality-core/tests/test_commitment_revisions.py \
  packages/reality-core/tests/test_commitment_actions.py \
  packages/reality-core/tests/test_application_tools.py \
  packages/reality-core/tests/test_return_announcement_adapters.py \
  packages/reality-core/tests/scenarios/test_b2b_operational_integrity.py
```

Run the repository PostgreSQL integration target for concurrency and recovery.

## End-to-end evidence

1. Receive tracked return into quarantine while identical stock exists elsewhere; scrap it and prove only returned identity changed.
2. Reserve and partially ship a commitment; review downward revision and prove the exact retained/released allocation and `reserved ≤ open`.
3. Cancel an unshipped commitment; prove reservations/holds release, stock/Document do not change, and history remains.
4. Simulate known validation failure, committed lost response, and true unknown; prove non-stranding, exact reconciliation, and replay protection respectively.
5. Repeat cancellation through MCP and Web and compare state and explanation links.

## Required gates

```bash
make spec-check
make lint
make test
make web-build
make docs-generate
make docs-catalog-check
cd apps/web && npm run i18n:audit
```

Use the CI PostgreSQL command rather than SQLite. Review against [spec.md](./spec.md), [data-model.md](./data-model.md), and [the action contract](./contracts/operational-actions.md). No task is complete while a required gate is red.

## Recorded evidence (2026-09-22)

- `pytest -q tests/test_commitment_revisions.py tests/test_commitment_actions.py tests/test_application_tools.py tests/test_return_announcement_adapters.py tests/test_returns.py`: **60 passed**.
- `pytest -q tests/tenant_isolation/test_families.py`: **10 passed** after registering the new cancellation proposal boundary in the tenant-isolation catalog.
- `make spec-check`: **passed**.
- `make lint`: **passed**.
- `make docs-generate`: **passed** and regenerated the command/resource/event references.
- `make web-build`: **passed**, including frontend formatting, **335 Node tests**, the complete i18n audit, and the production TypeScript/Vite build.
- `pytest -q tests/test_commitment_actions.py tests/test_application_tools.py`: **21 passed** after adding known-refusal restoration; the focused commitment file subsequently passed **6 tests**, including the preserved unresolved state for an unexpected effect-boundary failure.
- `node --test scripts/operational-integrity.test.mjs scripts/action-discovery.test.mjs`: **8 passed** and proves both commitment forms route through shared proposal preparation/confirmation.
- The Web production TypeScript/Vite build and all four-language i18n coverage pass with the new commitment forms.
- `pytest -q tests/test_returns.py tests/test_return_announcement_adapters.py`: **30 passed** with exact returned tracking identity included in review history and receipt verification.
- `pytest -q tests/scenarios/test_b2b_operational_integrity.py`: **2 passed** for the independent tracked-stock/revision/cancellation chain and the planted historical over-reservation read that remains visible and unmodified.
- `pytest -q packages/reality-core/tests/scenarios/test_b2b_operational_integrity.py packages/reality-core/tests/test_commitment_actions.py packages/reality-core/tests/test_returns.py packages/reality-core/tests/test_chat.py packages/reality-core/tests/test_capability_guidance.py`: **50 passed** after enforcing non-blank cancellation reasons, exact intent-correlated event verification, normalized lifecycle/effect/observation/remaining-work detail, Chat discovery parity, and the no-schema-shortcut guard.
- Interface contract matrix:

  | Interface | Normalized intent/review | Execution boundary | Receipt/state/explanation |
  | --- | --- | --- | --- |
  | Web | `deliveryActions.prepare` renders the shared review | Explicit `confirmed: true` with review token | Shared detail supplies lifecycle, recorded effect, observation, remaining work, and Inspector links |
  | MCP | `commitment_*_propose` schemas map to canonical application tools | `proposal_approve_and_execute` is separate from model-selected proposal | `proposal_execution_status` and shared detail reconcile opaque action/event identities |
  | Chat | OpenAI and Anthropic adapters receive the same MCP proposal schemas and capability guidance | Confirmation tool remains outside proposal selection | Same canonical proposal ID and reads; no chat-specific write path |
  | CLI | `commitment cancel` prepares and prints the shared review | `--yes` confirms the reviewed proposal | Uses the same proposal detail/result service |
  | API | Thin delivery-action prepare/review/approve endpoints | Approval requires review token and explicit confirmation | Returns the same shared proposal detail |

- `make docs-generate`: rerun after adding commitment action guidance; generated English/German tool references and catalog JSON are current in the worktree.
- `TEST_POSTGRES_DATABASE_URL=postgresql+psycopg://reality:local-only@localhost:54329/reality_test pytest -q tests/test_postgresql_integration.py -k 'concurrent_return_dispositions or concurrent_revisions or concurrent_cancellations_record_one_effect'`: **3 passed**; row locks serialize the returned Movement or Commitment and prevent over-disposition, over-reservation, and duplicate cancellation events.
- `pytest -q packages/reality-core/tests/test_returns.py packages/reality-core/tests/test_movement_explanations.py packages/reality-core/tests/test_commitment_revisions.py packages/reality-core/tests/test_commitment_actions.py`: **45 passed** with explicit returned-stock `before → effects → after` explanation and inherited identity in movement explanation.
- Focused Chromium evidence `apps/web/scripts/operational-integrity-browser.mjs`: **passed** against Vite on port 5177 using the real composed tool catalog. It exposed and then verifies the fix for the proposal-ID remount that previously returned the operator to the input form after preparing review.
- `node --test scripts/operational-integrity.test.mjs`: **1 passed** including the proposal-ID wiring regression guard.
- Final focused frontend gates after the remount fix: Python lint **passed**, i18n **2132/2132** in English/German/Dutch/Spanish, and the production TypeScript/Vite build **passed**.
- `git diff --check`: **passed**.
- Final implementation self-review: **passed** for the implementation boundary. The diff adds no migration or business-table field; uses opaque tenant-scoped proposal, commitment, reservation, Movement, event, and SourceRecord identities; preserves Movement as physical authority and Document as evidence rather than fulfilment authority; keeps reservation links directly on Commitment; and reconciles exact recorded effects without blindly replaying an unresolved proposal. The independent product/domain approval remains reviewer-owned in `checklists/integrity.md`.
- `make test`: **4,064 passed, 9 skipped, 0 failed** in 42:20. The preceding run exposed three committed PostgreSQL race fixtures leaking into the shared test database; each concurrency proof now owns a temporary database, and the exact race-then-affected-test ordering passed **88 tests with 1 skipped** before the uninterrupted full rerun.
- `make spec-check`: **passed** after final implementation changes.
- `make lint`: **passed** for the complete Core package after final test-isolation changes.
- `make docs-catalog-check`: **passed** against an isolated temporary Git index containing the intentionally changed generated files; the real index remained untouched. A second `make docs-generate` produced the identical SHA-256 diff hash `3161f25e9d3353293ceeddf428477d1147ba1eb3dc8aba8439f6f56cd312ebdf`, proving deterministic, current generated output before the check.
- `git diff --check`: **passed**.
