# Verification: Faster Quality Gates

1. Run `python -m unittest scripts/test_ci_backend_changes.py`.
2. Run `make spec-check`.
3. Prove the two shard manifests are complete and non-overlapping, then run each with
   `pytest -n 2 --dist worksteal --durations=20`.
4. Open a pull request and record backend job behavior for both classifier-only/backend
   changes and a representative frontend-only follow-up commit or local classifier proof.
5. Compare required backend job duration with the 11:01 baseline.

## Local verification evidence

- Backend path classifier: 5 tests passed.
- Spec policy, workflow YAML parsing, Ruff and diff checks: passed.
- Complete PostgreSQL suite with four work-stealing workers: 2,182 passed,
  9 skipped in 3:12. A preceding run reached 2:55 and exposed only the then-incomplete
  spec-policy metadata; no backend or parallel-isolation test failed.
- Baseline comparison: the complete local suite is approximately 69% faster than the
  PR #189 PostgreSQL step (3:12 versus 10:19). GitHub-hosted timing remains to be
  recorded from this feature's pull request.
- Initial GitHub four-worker experiment: all checks passed, but backend quality took
  10:36. One-runner parallelism saved only 25 seconds versus the 11:01 baseline, so the
  final design uses two independent runner shards instead.
- Final GitHub two-runner proof (run 34511988941): shard 0 passed in 6:16, shard 1
  passed in 5:42, and the required `backend-quality` aggregate passed in 4 seconds.
  Backend wall time is approximately 6:28 including change detection and aggregation,
  about 41% faster than the 11:01 baseline. The 34-second shard spread confirms the
  size-balanced partition is sufficiently even.
- A frontend-only classifier proof returns `changed=false`; in that path the test
  matrix is skipped and the same required aggregate emits the explicit successful
  skip result after change detection.
