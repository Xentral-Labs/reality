# Research

## Entry and consent
Decision: explicit ordinary-signup Playground flag recorded as a user security event; fixed owner request key passed to confirmed company setup after verification. Rationale: auth commits independently of lengthy demo setup; existing receipt, intent fingerprint and live completion marker support retries. Alternatives rejected: seed on GET, infer consent for historic users, duplicate fixture pipeline, new onboarding table. Research agents reviewed existing entry/company/UI paths without editing them.

## Managed AI
Decision: reserve one dispatch event under the account row lock, commit before provider call, count in the current UTC day. Rationale: across tabs/companies and process crashes no overspend; provider failures can already incur cost and therefore count. Caller account is authoritative when authenticated; owner is fallback for internal service calls. Own provider keys and non-trial business accounts preserve existing behavior. Free-signup accounts remain limited in subsequently created ordinary companies to prevent bypass. Alternative rejected: browser counters, chat-message counts (no account attribution and deletions), provider-call transaction lock, new quota schema.

## First value and voluntary support
Decision: existing read-only operational destinations; successful current-tenant read signals a task result, delivery requires a detail. Prompt dismissal stored per account in this browser, with safe handling when storage is unavailable. Rationale: no AI dependency or fabricated success, no new account preference schema. No telemetry provider, auto-star or star gate.

## Enable policy
Decision: missing Playground flag enables practice/free entry; explicit false retains disable. Admission rules remain feature 189. Rationale: open default must work for the complete journey, not just authentication. Existing capacity/lesson restrictions remain.
