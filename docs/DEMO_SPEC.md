# Interactive Demo

Goal: ~1–2 minutes, mostly Enter-to-run. If no tenant, offer `Acme Bikes GmbH`. If tenant is non-empty, never destroy data; offer a fresh demo tenant.

Manifest contract: `guided-demo-v1`. A real execution inventories 3 Parties, 1 Item,
1 Location, 1 SourceRecord, 1 SourceStream, 1 ImportJob, 1 Document, 1 DocumentLine,
2 Commitments, 1 Reservation, 1 Movement, 12 BusinessEvents, 1 ChatSession, and
2 ChatMessages; it currently produces zero Facts and zero LedgerEntries. The comparison
groups these into reference data, Source, Evidence, Reality, derived outcomes, and
explanation. New or removed families require an explicit manifest-version review.

Product Web must keep two distinct onboarding choices: an empty company, or this guided
demo after explicit confirmation. Successful demo creation opens the normal product and
its Inspector; cancellation issues no mutation.

Every step: business event → suggested CLI command → `[Enter] Run [E] Edit [Q] Quit` → result + primitive explanation.

1. Create Augsburg Warehouse.
2. Create Bike Parts GmbH supplier.
3. Create BIKE-LIGHT.
4. Receive opening stock 20 (Movement).
5. Ingest `fixtures/shopify/order_10473.json`: Müller orders 30 due tomorrow.
6. Show SourceRecord → Document → Line → outgoing Commitment.
7. Reserve 20; show shortage 10.
8. Purchase 20 due tomorrow: incoming Commitment.
9. Receive 20; fulfill supplier Commitment.
10. Reserve remaining requirement.
11. Ship 30; fulfill customer Commitment.
12. Run `explain commitment` and `timeline`.

`demo --auto` must call exactly the same application services and is the golden integration path.

The browser has a second guided path since spec 182: the storyline
`packages/reality-core/storylines/order-to-close.storyline.yaml` plays an order from
creation to the month-end review in a practice company, with the calls and the recorded
changes of every chapter shown beside the story. It runs through the same application
services as this demo and touches no business company (`docs/features/learning-playground.md`).
