# Simulator spectator

A separate local, read-only viewer for existing and growing simulator artifacts. No database, actor token, business mutation or Reality product UI is involved.

From `packages/reality-core`:

```sh
../../.venv/bin/python -m scenarios.company_simulator.viewer
```

Open **http://127.0.0.1:8765**. Default artifacts are resolved from the repository, independently of current working directory. Use `--root /path/to/journals --port 8766` to select another root. Direct run directories and one grouping level (such as `complete_acceptance/prompt`) are recognized. Stop with Ctrl+C.

## Views
- **Company timeline**: recorded business events, original customer messages, last independent checkpoint, customer delivery goals and exercised/planned case families.
- **Customers**: select an explicitly recorded customer, read original sender/recipient/subject/body and related activity.
- **Suppliers**: select a supplier and inspect purchase, receipt, invoice and payment activity; supplier messages appear only when actually present in the journal.

Messages and accepted business actions are distinct. The complete v2 profile records customer follow-ups, supplier notices and simulated baseline-agent replies; custom-agent replies remain proposed drafts. Older complete journals and the Shopify/operational profiles keep their original coverage. The UI explicitly labels simulated local replies and unsent drafts. Empty-state copy states this rather than fabricating conversations. Optional future message journal `party_id`, `direction` and `status` fields are displayed exactly as recorded, including proposed outgoing drafts. Business proposal acceptance never implies an email was approved or sent.

Status is the recorded result, not a new core verification. No final report means **unfinished**, not verified process liveness. Check the observation timestamp. The browser polls every five seconds; selected run/partner remain selected. Checkpoints and case coverage remain separate from business-goal misses. In older unfinished runs without world snapshots, accepted tool operations are labelled separately and do not claim business-case coverage.

New complete/Shopify runs publish atomic `spectator.json` snapshots after each checkpoint and at terminal outcomes. Only released world observations, references, goals and coverage are exported. Export failures do not change business behavior; `spectator_error` in the final report records them. This is not durable execution/resume or real-time pacing.

## Browser proof

With Chromium and Playwright installed:

```sh
PLAYWRIGHT_MODULE=/path/to/playwright-core PLAYWRIGHT_EXECUTABLE=/path/to/chromium node scenarios/company_simulator/viewer/browser_check.mjs
```

The script creates disposable synthetic artifact fixtures, starts a loopback viewer, checks selection, explicit partner filtering, original text, draft/send separation, five-second polling, incomplete writes and a narrow viewport, then removes fixtures. If retained `complete_acceptance/prompt` artifacts exist, it also checks that historical v1 month's ten messages, twenty-two case families and EUR190 closing cash. Screenshots and result are saved under ignored `artifacts/company_simulator/viewer/`.

To verify the new complete-v2 prompt month, set `SIMULATOR_RETAINED_RUN` to its saved artifact directory when running `browser_check.mjs`. The proof expects its 106 messages, customer/supplier filtering, 28 case families and unchanged closing cash190; older v1 prompt artifacts remain supported.

## Company stories: watch or replay

Open **http://127.0.0.1:8765/stories** after starting the viewer above. Select a complete-company run. **Live watch** polls journals every five seconds and follows the latest complete checkpoint, preserving the open story. **Replay recording** enables the slider, **Play recording**, **Pause replay** and **Next day**; incoming updates do not advance the selected replay day. Only available checkpoints are replayed.

Start the simulator separately with the CLI in the parent README. Browser controls never start, pause or change simulator execution. An unfinished journal does not prove process liveness; observation timestamps and read notices remain visible. Unsupported profiles use the original spectator at `/`.

Info panels show exact order, message and accepted-effect references. Copyable Reality paths are unverified targets; archived test companies may have been rolled back.

Live/replay browser regression (start the viewer first and retain a complete-v2 prompt month):

```sh
PLAYWRIGHT_MODULE=/path/to/playwright-core SIMULATOR_VIEWER_URL=http://127.0.0.1:8765 node scenarios/company_simulator/viewer/stories_browser_check.cjs
```

`SIMULATOR_STORY_RUN` defaults to `correspondence_acceptance/prompt`. The proof intercepts browser GET responses to model growing checkpoints without modifying captured artifacts.
