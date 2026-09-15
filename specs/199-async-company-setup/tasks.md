# Tasks: Company setup does not seed inside the request

1. Service and job tests first: deferred receipt, single enqueue, handler effect and
   re-run, refusal at enqueue and claim, retry escape hatch, immediate empty company.
2. Make `initialize_profile` and `_finish_live_setup` transaction-bound (`_commit`).
3. Add `initialize` to `start_run` and use the seam in `create_company`.
4. Register `company_setup.initialize` and route its authorization in `_owner`.
5. Follow the receipt in both preparing screens.
6. State the proxy read timeout.
7. Update the scheduled-jobs and company setup contracts and the coverage matrix.
8. Run the focused suites, web checks, browser run and the full PostgreSQL suite.
