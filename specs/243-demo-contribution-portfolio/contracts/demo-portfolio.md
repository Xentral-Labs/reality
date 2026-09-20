# Canonical Demo Contribution Portfolio Contract

## Profile boundary

The contract applies only to newly initialized `international_demo` profile version 3 companies. Empty companies, execution fixtures, historical version-2 companies, and continuous `demo_data` arrivals are unchanged.

## Manifest contract

`initialization_progress.costing_cases` retains the existing named cases and adds five stable complete-case entries. Each complete entry exposes opaque references needed to inspect its invoice line, inventory review, commercial match, and contribution review. Human-readable source and document references identify the scenario for a demo operator but never replace those opaque links.

## Outcome contract

Together with `fixture_a`, the profile exposes at least six complete reviewed invoice-line contributions. The set includes:

- a healthy positive DB2 outcome;
- a lower positive DB2 outcome;
- a negative DB2 outcome;
- a complete outcome with every selling-cost category reviewed as zero;
- an allocated-cost-heavy outcome;
- fixture A's existing mixed direct and allocated outcome.

For every complete outcome:

```text
DB1 = received net revenue - consumed acquisition cost
DB2 = DB1 - reviewed direct selling costs - reviewed allocated selling costs
DB2 rate = DB2 / received net revenue
```

The shared contribution read returns the exact inputs, results, currency, cutoffs, freshness, and trace. It returns no value where a required basis remains unknown.

## Replay and isolation contract

- Replaying initialization reuses the completed run and creates no duplicate business records.
- All portfolio records and reads remain tenant-scoped.
- No adapter receives a private seed or direct persistence path.
- Existing missing-cost and late-cost/return cases remain truthful.
- Continuous Demo Data retains missing-cost semantics and is never auto-reviewed into this portfolio.
