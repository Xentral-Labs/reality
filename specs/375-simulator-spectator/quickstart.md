# Watch simulator runs

From the repository root:

```sh
cd packages/reality-core
../../.venv/bin/python -m scenarios.company_simulator.viewer
```

Open http://127.0.0.1:8765. Use `--root /absolute/path/to/artifacts --port 8766` for another journal directory. Stop the viewer with Ctrl+C. It does not start, stop or mutate a simulator. Existing complete_acceptance grouping is recognized automatically.

Select a run; inspect Company timeline, Customers and Suppliers. Messages show original source fields. Actions remain separate. The complete v2 profile adds supplier notices, customer follow-ups and simulated baseline replies. The UI labels simulated local replies and unsent custom drafts; older profiles/journals keep their original coverage. Empty states remain explicit.

For new runs, refresh follows atomic daily spectator snapshots. No final report means unfinished, not guaranteed running. Check the last observation time. The current compressed controller may finish before opening the viewer; saved history remains available.

Verification: `../../.venv/bin/pytest tests/scenarios/test_simulator_viewer.py tests/scenarios/test_complete_company.py tests/scenarios/test_shopify_company.py` with the repository test PostgreSQL available. Viewer startup itself needs no PostgreSQL.
