# Research: Proposal Decision Policy

## Decision: Preserve authorization while making guidance accurate

The independent authority audit found cost owner, company owner, delivery membership,
account identity, membership owner and private-report author conditions.
Generic required_principal alone cannot faithfully represent them. Use a derived
immutable policy with separate authority and decision/access descriptions.

## Decision: Distinguish approval and rejection

reject_proposal has no finance/cost owner check. Adding it would change rights.
Expose rejection as existing access-context authority; change the misleading UI
sentence that currently says the owner must approve or reject.

## Decision: Keep transaction boundaries and exceptions

Costing checks active user plus active owner membership with a bounded profile
exception. require_owner checks active owner membership. Reviewed delivery allows
trusted local calls and platform admin exceptions. Finance/credit identity-free
calls require disabled authentication. Report checks require the original active
author. Retain each check at its current phase and retain specialized validators.

## Alternatives considered

- Rename only required_principal: rejected because execution and guidance still drift.
- Add a new permission/delegation engine: rejected because no approved use case.
- Enforce human presence from approved=true: rejected because this is no proof.
- Apply owner rules to rejection: rejected because it changes existing access.

No unresolved research questions. The audit is read-only and introduced no files.
