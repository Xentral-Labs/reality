# Baseline Starting State

**Captured**: 2026-08-31
**Repository HEAD**: `846c899`
**Purpose**: Separate specification-baseline work from pre-existing or independently
developed product changes in the shared working tree.

## Product paths already modified before baseline-spec execution

- `backend/migrations/versions/0025_user_language.py`
- `backend/src/reality/agent/mcp_chat.py`
- `backend/src/reality/services/core.py`
- `backend/src/reality/services/file_interpreters.py`
- `backend/src/reality/web/app.py`
- backend test files changed by the preceding quality-baseline repair
- `frontend/src/Auth.tsx`
- `frontend/src/login.css`
- generated `frontend/dist/` assets and `frontend/tsconfig.tsbuildinfo`

These paths are not outputs of tasks T012-T043. The isolated no-product-change proof
compares the file set produced by baseline-spec tasks against this snapshot, rather
than treating the already-dirty working tree as baseline output.

## Allowed baseline output roots

- `specs/`
- `docs/SPEC_COVERAGE_MATRIX.md`
- `scripts/check_spec_policy.py`
- `backend/tests/test_spec_policy.py`

Any new modification outside these roots during baseline execution fails FR-012 unless
the owner approves a separate change specification.
