# Research decisions

Read-only Spec-Kit research agent inspected shared discovery, order readiness and both
provider loops on merged main e2c48e15.

- Decision: extend existing discovery pages, not introduce a daily report tool.
  Rationale: returned-row type counts are sufficient; no unbounded scan or new grant.
  Alternatives: full totals/snapshot report expands the contract unnecessarily.
- Decision: count only shown records, excluding the lookahead. A final cursor page
  still omits preceding records. No upstream completeness inference.
- Decision: mark historical cause unknown for positive remaining fulfillment, while
  retaining current canonical blockers. Ready does not explain why shipping has not
  happened; missing outbound objects do not prove a conversion requirement.
- Decision: native return context uses public discovery. No adapter arithmetic.
  Prompt guidance helps use the ready observations but cannot guarantee arbitrary prose.
- Rejected regex output rewrite and second model judge: neither proves business truth.
