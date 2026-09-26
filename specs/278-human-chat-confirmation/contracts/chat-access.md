# Built-in Chat Access Contract

## Production company

- Offered: `read`, `propose`.
- Not offered: approval/execution, rejection or any settlement alias.
- Proposal result: pending exact decision with no business effect.
- Next action: authenticated human opens canonical decision review.

## Playground company

- Offered: `read` only. Proposal and decision tools are absent.

## External MCP client

- Unchanged; tools follow its tenant-scoped access token.
- Token attribution never claims a human identity.

## Human Web review

- Unchanged authenticated confirmation/rejection via shared application service.
- Permission, owner, review-token, stale-state and idempotency checks remain mandatory.

## Provider attempt outside the contract

An unoffered settlement tool is refused before application decision execution. Proposal state,
targets and Business Events remain unchanged.
