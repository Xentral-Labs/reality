# Research: Shopify Update Guard

- Decision: Guard source versions greater than one before interpreting new Evidence.
  Rationale: This covers consecutive updates and failed/pending predecessors without
  inventing amendment semantics. Existing interpreted versions return first.
  Alternatives: Comparing selected fields risks missing business meaning; following
  only the predecessor Document misses a chain containing an unreviewed update.
- Decision: Reuse needs_review and a fixed safe message for the Shopify guard.
  Rationale: Existing Web, HTTP and agent coverage already expose review outcomes.
  Alternatives: A failed job implies a transient retryable error; a new queue/schema
  adds no value for this bounded protection.
- Decision: Completed review is terminal until explicit retry.
  Rationale: Repeated processing must not throw or duplicate attempts. Explicit retry
  remains available but cannot bypass the guard.

No unresolved research questions, vendor API assumptions, or technology choices.
