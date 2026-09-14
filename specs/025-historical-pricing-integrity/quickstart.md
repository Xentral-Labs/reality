# Quickstart: Validate Historical Pricing Integrity

## Focused pricing proof

```bash
cd packages/reality-core
pytest -q tests/test_pricing.py
```

Expected: a server-validated selected entry is retained on an agreed line; mismatched or
foreign attachment fails atomically; an agreed linked line survives list lifecycle/default changes, assignment and
membership changes, new tiers, and effective-time changes; new work resolves its own
price; manual prices remain valid; sales/purchase and tenant boundaries remain separate.

## API and Inspector proof

```bash
cd packages/reality-core
pytest -q tests/test_master_data_api.py -k pricing
```

Expected: agreed values and retained identity remain distinct from a current comparison,
and foreign line/entry identities disclose nothing.

## Regression and policy proof

```bash
cd packages/reality-core
ruff check .
pytest -n 2 --dist loadscope
cd ../..
python3 scripts/check_spec_policy.py
git diff --check
```

Expected: complete backend, lint, Spec policy, and formatting gates pass; no migration or
schema change exists.

## Manual review

1. Open a document containing a line with a retained pricing-entry identity.
2. Confirm the agreed quantity, unit price, gross amount, unit, and currency lead.
3. Change pricing applicability for new work and reopen the old document.
4. Confirm the old agreement is unchanged and any fresh comparison is labeled current.
5. Repeat with a manually priced line and confirm no pricing provenance is invented.

Only after automated evidence and final product-owner review pass may `004/FR-014` and
only its coverage-matrix gap be marked verified.

## Implementation evidence (2026-09-02)

- Ruff: passed for the complete Core source and test tree.
- Focused pricing, correction, API, and migration proof after final review: 41 passed.
- Complete PostgreSQL suite excluding the unrelated Atlas policy check: 217 passed,
  7 skipped.
- Complete suite before that exclusion: 221 passed, 7 skipped, with only the new
  tenant-catalog count and the pre-existing Atlas coverage-matrix check failing. The
  catalog count was corrected and its affected tests subsequently pass.
- Schema review: the existing DocumentLine fields are sufficient; no model column,
  table, or Alembic revision was added.
- Web build: N/A. The Inspector change is server-rendered API presentation and no Web
  client source or contract was changed.
- Final Spec policy and diff checks pass. Concurrent Atlas work moved its contract to
  `docs/agreements/atlas_reality_o2c_test.md`; Spec 025 did not modify that unrelated
  content.
- Final review found and fixed two compatibility cases: free-form legacy document dates
  remain accepted when no pricing entry is attached, and presentation-only correction
  retains historical pricing provenance after current default applicability changes.
