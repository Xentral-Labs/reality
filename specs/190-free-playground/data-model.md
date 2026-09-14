# Data Model

No schema expansion. `SecurityAuditEvent` records `account.trial_started` for every new ordinary public signup (independent of optional demo consent), `playground.requested` for the explicit ordinary-signup consent and `playground.ai_dispatched` for accepted managed usage, scoped by existing `user_id`, `tenant_id`, `occurred_at`. No prompts, credentials or business payloads in usage detail. Current-day dispatch counts are a read-time observation, not persisted remaining-balance authority.

`PlaygroundRun` retains owner, canonical tenant, fixed `client_request_key`, initialization status and existing intent/live completion JSON. Entry never invents a second tenant identifier or reopens an archive. `AppUser` row locking serializes account allowance reservation; provider runs after commit.

Browser localStorage key includes account ID and stores only prompt dismissal. It is optional device-local UI preference, not a quota or business fact. Active task is transient and tenant-scoped.
