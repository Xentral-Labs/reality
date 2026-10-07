# Enterprise CI gate isolation

Spec impact: none. This is build/test maintenance restoring the existing declared
isolated performance measurement. No product service, schema, business rule,
acceptance threshold or test scenario changes.

After the compatibility rebase, CI run 37594673723 passed all functional, browser,
frontend and documentation jobs but failed the Control Tower enterprise live p95
gate: 3.565301439 seconds against the unchanged three-second threshold. Opening
p95 was 2.099883243 seconds; all twelve five-second cycles and final committed-order
visibility passed. The full failed observations and runner conditions are retained
in `ci-enterprise-shared-runner.json` and the original CI job 112704340083.

The profile file declares an isolated 10,000-active / 100,000-historical-order /
500,000-observation fixture with ten browsers, four independent component reads,
480 live requests and twelve concurrent canonical bookings. CI previously ran it
with `pytest -n 2` alongside unrelated regression fixtures. It now owns a separate
matrix runner/database, with the same PostgreSQL image, Python setup and measured
internal concurrency. The other four shards retain their existing worker count.
The aggregate backend gate requires success from every matrix entry, including
`enterprise`; failures cannot become skips or retries inside the timing test.

A shell-execution coverage proof with a recording pytest substitute verified all
555 backend test files are scheduled exactly once across the five entries, only
the enterprise entry runs without xdist, and both ordinary and enterprise failures
propagate as nonzero job exits. Local isolated and final CI measurement outcomes
are recorded in PR #380. The original Business capacity measurements and open
SC-004 acceptance are unchanged; a green isolated Control Tower profile does not
certify the Business million-order workload or a production rollout.
