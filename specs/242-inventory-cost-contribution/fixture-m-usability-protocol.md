# Fixture M moderated usability protocol

Status: ready to run; no participant sessions recorded yet.

## Purpose and pass criterion

Determine whether an operations user unfamiliar with the implementation can find one complete
demo order's DB1 and DB2, explain one deducted cost and reach its source evidence without developer
assistance. Run five independent sessions. The feature passes SC-002 only when at least four
participants complete every task correctly within two minutes.

## Participant and environment controls

- Recruit five people who perform or supervise ecommerce operations and did not implement spec 242.
- Use the same deployed build, canonical `international-v2` demo profile and complete fixture-A order.
- Start each session signed in to the demo company with the Sales workspace visible and no record open.
- Reset navigation, filters, language and browser zoom between sessions. Do not reset business data.
- Record build identity, demo run ID, browser, viewport, UI language and session date.
- Do not use production company data. Do not expose participant personal data in repository evidence.

## Neutral moderator script

Read exactly:

> This is a test of the product, not of you. Starting from this page, find the complete demo order.
> Tell me its DB1 and DB2. Explain one cost deducted in either result, then open the original source
> evidence supporting that cost. Work as you normally would. I cannot explain where controls are,
> but you may stop at any time.

Start the timer after the final sentence. Stop it when the participant opens the correct source
evidence or at 120 seconds. The moderator may repeat the task verbatim and answer procedural or
consent questions, but must not name a page, control, value, record type or navigation path.

## Correct outcome

For the complete fixture-A position the participant must state DB1 `570 EUR` and DB2 `456 EUR`,
identify one actually included deduction (for example the reviewed consumed acquisition cost or an
evidenced selling-cost component), and open the corresponding source evidence through the product's
explanation/Inspector path. A guessed value, a technical ID without the source, an unrelated source
record or a value read from moderator material is incorrect.

## Session record

Create one row per participant. Use anonymous participant codes only.

| Participant | Operations role | Build / demo run | Browser / viewport / language | DB1 correct | DB2 correct | Included cost explained | Correct source opened | Seconds | Assistance or failure notes | Pass |
|---|---|---|---|---|---|---|---|---:|---|---|
| P1 |  |  |  |  |  |  |  |  |  |  |
| P2 |  |  |  |  |  |  |  |  |  |  |
| P3 |  |  |  |  |  |  |  |  |  |  |
| P4 |  |  |  |  |  |  |  |  |  |  |
| P5 |  |  |  |  |  |  |  |  |  |  |

A participant passes only when all four correctness columns are yes, elapsed time is at most 120
seconds and no disallowed assistance was provided. Record observable failure points, not inferred
motives. Preserve screenshots or recordings only with participant consent and outside the repository
when they contain personal information.

## Result summary

- Sessions completed: 0 / 5
- Successful sessions: 0 / 5
- Median completion time: not measured
- SC-002 decision: **OPEN — study not yet run**
- Product issues observed: not measured
- Follow-up owner and date: unassigned

The moderator signs and dates the completed record. Automated tests, fixture assertions and a
developer walkthrough must never populate the participant rows or change the SC-002 decision.
