# Verification

Base: native392 commit9ab2648472746b55d7be26f06602364f16ea7d5f. Scope is a
read-only current-native capability; no existing runtime, grant or provider changed.

- Test-first collection failed because the new domain/service did not exist.
- Final focused suite:10 passed, including three actual two-session changes,
  no-write snapshots and actual authenticated MCP initialize/list/call, unauthenticated
  refusal and ungranted generic-confirm denial. Frozen JSON schemas/examples validate.
- Related390/391/392 suite:127 passed before the final output-schema-only bound and
  additional schema/example test; final focused suite covers those last changes.
- Normal application/MCP permissions/read/HTTP/refusal boundaries:115 passed.
- Full Ruff, spec policy and business annotations: green (699 described functions,
  115 described tests, zero missing).
- Web Node22:483 tests passed, format/i18n audit and production build green.
  Initial new-refusal localization omissions were fixed in the existing dictionary;
  the initial Node20 invocation was an environment mismatch, not accepted evidence.
- Docs:16 Python reference tests,145 Node tests, format and production build green.
  The maintained generator uses its pinned formatter; unrelated format churn removed.
- Existing SQLAlchemy deprecation/analytics warnings and bundle-size warnings remain.

All database proofs used owned disposable PostgreSQL databases; they were removed
by the harness. The private test container is stopped after checks. No existing
company database, live Shopify/Reality operation or paid model call was used.

Independent root source review cleared the bounded tenant/reference/source read;
the read is optimistic, not serializable final-effect authorization. Native392
must independently revalidate and lock before any acceptance. Full hosted suite
and final PR review remain required; local focused checks do not substitute for it.
