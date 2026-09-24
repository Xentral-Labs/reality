# Contract: Ordinary-Company Cost Guidance

## Purpose

Turn a truthful but uninitialized/incomplete cost read into an actionable explanation without
creating financial authority or a second costing implementation.

## Read envelope

For the bounded requested inventory or contribution scope, the read identifies:

- opaque scope and subject identities;
- current/historical freshness and cutoff;
- completed evidence/review/publication stages;
- exact missing evidence or owner decision;
- the next supported owner-reviewed operation, when one exists;
- explanation links to held evidence and retained reviews;
- independent availability/coverage for acquisition, inventory, DB1 and DB2.

The envelope performs no writes and does not promise that the next proposal will be accepted if
state changes before review.

## Authority

Agents may inspect guidance and prepare existing cost-change proposals. Only an authenticated
active owner confirms attribution, completeness, ownership, tax, conversion, valuation or policy
decisions. Purchase prices and price lists do not become historical actual acquisition cost.

## Outcomes

- Complete supported evidence and review may yield an explainable retained result.
- Missing actual cost keeps acquisition/inventory/DB1 unavailable.
- DB1 may be available while DB2 remains partial or unavailable for missing selling-cost scope.
- Unavailable never renders as trusted zero.
- Canonical demo readiness continues to follow spec 251 and does not grant ordinary companies
  automatic review authority.
