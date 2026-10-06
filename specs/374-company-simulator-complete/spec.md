# End-to-end company simulator profiles

**Language**: English

## Context and Intent
The user requests that the previously listed missing company flows become executable parts of the reactive rehearsal. Preserve the small operational profile as regression; provide an extended default month plus a synthetic Shopify profile using existing supported intake and settlement paths.

## User Scenarios & Testing
A prompt operator fulfills feasible goals, purchases shortages, invoices completed shipments, pays suppliers and responds to physical returns separately from financial credits/refunds. A delayed/idle operator may miss goals without corrupting Reality. An incorrect address or failed carrier arrival must not count as success. Independent daily checkpoints cover both operational and financial balances. External operators receive released observations and propose exact actions subject to supervised approval.

## Requirements
- **FR-001**: Add a reviewed 30-day extended general-company profile in an ordinary local test company preserving the spec373 profile.
- **FR-002**: Retain released synthetic customer emails as lossless local sources. Cover partial supplier receipts, supplier delay, partial customer shipments, unshipped cancellation, announced/arrived returns, stock-count loss and warehouse transfer through production tools.
- **FR-003**: Cover sales/supplier invoices, partial/full customer payments, supplier payments, sales credits and customer refunds with explicit authored source amounts and independent open-balance/account oracles.
- **FR-004**: Dispatch through outbound plans; verify preserved recipient/address and package-level delivered/failed evidence. Grade full quantity, correct destination and arrival deadline separately from core correctness.
- **FR-005**: Keep a visible released-world view isolated from private future events and oracle; support a custom operator through a supervised exact-action review interface without implicit blanket AI approval.
- **FR-006**: Add a clearly synthetic Shopify-shaped profile using existing production supported intake/payout paths, preserving raw payloads and separating charges/refunds/fees/payout amounts. Provider statements arrive even without agent invoices; Known payments without invoices remain held/unallocated; unknown customer references remain unmatched and explain the independent clearing imbalance. Do not claim authentic Shopify export compatibility.
- **FR-007**: Record exact receipts, daily operational/financial checkpoints, coverage inventory, failures/unknown outcomes and business-goal results; stop core mismatches without retrying uncertain actions.
- **FR-008**: Include meaningful regression proofs for delayed/idle/wrong-destination behavior and oracle corruption; run the complete backend suite.

- **FR-009**: Extend the complete profile with released customer cancellation/return/status messages, supplier confirmations/delay/receipt messages and local baseline-agent replies. Preserve exact payloads as normal Sources with explicit party/order references and thread/reply identities. All communication is synthetic local evidence, never a production email authorization or real send. Idle/custom operators receive no invented replies; custom operators may explicitly record reply drafts. Message evidence alone never changes stock, commitments or finance. Supplier notices release only at their authored time.

## Success Criteria
Extended month exercises each stated flow with traceable receipts and independently reconciled stock/open quantities/invoice balances/balanced postings. Customer outcomes depend on actual shipping and package evidence. Synthetic Shopify settlement differs from individual customer payments and fees are visible. The legacy operational comparison stays green.

## Requirement Traceability
FR-001–FR-005, FR-007–FR-009: tests/scenarios/test_complete_company.py, scenarios/company_simulator/complete.py, complete_world.py, complete_observer.py, bridge.py and profiles/general_company/complete.yaml. FR-006: tests/scenarios/test_shopify_company.py and profiles/shopify_company/.

## Non-Goals
No assertion of every possible industry/regulatory business process. No real external mail/shop/provider sends, payroll/tax filing, durable unbounded daemon or fabricated authentic Shopify formats. Simulated email correspondence is retained local source evidence. Recovery after an uncertain accepted effect requires reconciliation, not automatic replay.

## Assumptions and Dependencies
Existing tools cover the stated flows; no schema expansion is planned. Application clocks remain real and ordinal simulator timestamps live in artifacts. Source-stated totals stay authoritative. Authentic Shopify originals are unavailable; existing fixtures are explicitly synthetic. Live custom-operator actions require exact review or an existing authorized mandate; read access does not approve writes.

## Live-runtime scope handoff

The approved sustained external-agent and simulated-mailbox direction is specified in [spec376](../376-live-company-simulator/spec.md), including manual preview/injection. This specification's finite-run/viewer implementation is baseline evidence, not proof of continuous pacing, durable resume or external-agent inbox integration. Those remain pending; do not label the current PR a complete live runtime.
