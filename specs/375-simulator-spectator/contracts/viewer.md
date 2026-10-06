# Viewer contract

CLI: `python -m scenarios.company_simulator.viewer --root PATH --port 8765`. Default root resolves to repository artifacts/company_simulator independently of cwd. Bind 127.0.0.1 only. No business/database configuration required.

- `GET /`: static entry; `/app.js` and `/style.css` fixed assets.
- `GET /api/runs`: `{runs: [...], notices: [...]}`. Eligible direct child directories, or immediate children of one grouping directory (e.g. complete_acceptance). Exclude escaping symlinks. Run keys are root-relative paths, not human run identity.
- `GET /api/runs/RUN_KEY`: `{manifest, report, checkpoint, snapshot, parties, messages, timeline, operations, notices, summary}`. Only known files read. Unknown/unsafe paths return 404. Partial optional files produce notices rather than invented values.
- Other routes: 404. Mutating HTTP methods: 405. Cross-origin/local Host failures: 403. JSON and assets carry no-store/nosniff/CSP/frame denial, no CORS permission. UI text is always inert.

List records include artifact key, original run ID, profile, operator, configured days and terminal-report availability. Summary separates terminal state, recorded core check, last observed timestamp/day, checkpoint quantities, goals and authored case-family coverage. No response claims verified worker liveness.

The UI polls at five seconds and permits explicit refresh. Selection is preserved; late fetches cannot overwrite a newly selected run. Customer/supplier views show mailbox and separate business activity. Missing supplier mail/agent replies are stated explicitly. Technical originals are expandable.

Recorded `simulated` outgoing messages display “Simulated locally · no real email sent”; `proposed` outgoing records display “Reply draft · not sent”. Original thread/reply identity remains expandable; a recorded reply reference shows its recorded parent subject when available. Simulation day is displayed separately from the actual journal timestamp. These are local source states, never inferred production approval or delivery.

Story routes: fixed `/stories`, `/stories.js`, `/stories.css` assets and `GET /api/stories/RUN_KEY`. The response includes manifest, snapshot, report, complete checkpoint/message/action journals and notices using the existing safe ArtifactStore loader. Watch polls every five seconds; replay controls presentation only.
