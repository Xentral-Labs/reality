# Feature: Tenancy

Every business record belongs to exactly one tenant. Application services receive the
tenant ID explicitly and scope both lookup and mutation; `Session.get()` without a
tenant check is not an application-level lookup.

V0 supports create, list, use, and current in the CLI. Two tenants may reuse names,
SKUs, document numbers, and external IDs. Cross-tenant reads return not found and
cross-tenant links/mutations fail without revealing the foreign record.

Acceptance tests cover every public repository/service family, inventory aggregates,
chat sessions, web routes, and duplicate external identifiers across tenants.

## Company membership invitations

An active company owner may invite a normalized email address. The invitation is
tenant-scoped administrative Evidence and creates no account link or membership before
the matching verified recipient explicitly accepts. Known and unknown accounts expose
the same owner-visible pending state. Resend rotates the secret generation; only a
one-way token hash and token-free delivery intent persist.

Inspecting a usable invitation names the company and the invited address to whoever
holds that secret, so invite-bound registration presents the address instead of asking
the recipient to retype it. An unusable invitation names neither.

Membership roles are `owner` and `member`; lifecycle states are `active` and `removed`.
Only owners administer invitations. Owners and platform administrators may remove an
active non-owner, while owner removal or transfer is outside this contract. Acceptance
reactivates the existing tenant/account membership identity after removal. Every read,
mutation, delivery, and audit query remains tenant-scoped.
