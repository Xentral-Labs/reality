# Validation

See [the start guide](../../packages/reality-core/scenarios/reference_week/README.md).

```bash
make spec-check
make lint
cd packages/reality-core
../../.venv/bin/pytest tests/scenarios/test_reference_week.py -q
```

The exact local command-line fixture requires an existing eligible user, an explicitly
selected migrated local PostgreSQL database and `--confirm`. No schema/user bootstrap
is hidden in the runner. Day expected 0/6/0; week expected 7/4/4. Deliberately changing
E08's expected physical A to 999 must fail at E08, report actual 6/delta -993 and leave
purchase order count zero because E09 was never emitted. Observe retained source and
proposal IDs in the report; preparation has zero accepted business-effect delta.

Initial acceptance evidence (2026-10-05): six tests passed on isolated PostgreSQL,
including day/week, wrong oracle stop, fresh companies/read-only observer,
confirmation refusal and invalid fixture refusal. Final gates are tracked in review.md.
