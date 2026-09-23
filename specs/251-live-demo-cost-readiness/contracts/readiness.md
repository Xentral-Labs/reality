# Live Demo Cost Readiness Contract

## Company setup receipt

The existing company-setup response keeps its route and top-level shape. While the
canonical profile is initializing, `preparation` identifies the current stage. The
calculation stage is complete only when:

1. every item with positive physical stock belongs to a supported reviewed inventory
   scope at the admitted event cutoff;
2. every opaque invoice-line identity in the immutable contribution-demo manifest has
   current DB1 and DB2 observations;
3. coverage counts equal their expected counts; and
4. live simulation has not admitted a newer event before the verified marker commits.

On failure, `status` remains `initialization_failed`, `destination` remains absent and
`error_code` plus a bounded diagnostic distinguish evidence-missing, calculation-failed
and retryable worker failure. Monetary zero is never used as an error signal. After
success is observed, automatic entry waits at least 1.5 seconds so the completed
four-step sequence remains perceivable.

## Cost readiness summary

The setup profile manifest may expose:

```json
{
  "cost_readiness": {
    "version": 1,
    "state": "ready",
    "event_sequence": 123,
    "inventory": {"expected": 18, "current": 18},
    "contribution": {"expected": 6, "current": 6},
    "diagnostics": []
  }
}
```

Terminal states are `ready` or `failed`; transient presentation states are derived from
the setup job (`queued`, `preparing`, `retrying`). Diagnostics are bounded opaque scopes
plus stable evidence reason codes; they contain no foreign-tenant existence signal.

## Continuous freshness

After one synthetic intake occurrence commits, reads use the shared costing services to
compare each retained scope with only its relevant physical and reviewed-cost events:

- `current`: the retained review still covers the latest relevant admitted cutoff;
- `updating`: an explicitly confirmed replacement review is being processed;
- `failed`: explicit replacement review processing failed and the prior result remains;
- `stale`: newer relevant evidence exists and requires explicit owner review;
- `evidence_missing`: no supported reviewed basis exists.

Normal synthetic orders, invoices, credits and payments do not create financial review
authority and therefore neither stale unrelated scopes nor enqueue a pretend review.
No adapter may translate the last four states into a trusted numeric zero.
