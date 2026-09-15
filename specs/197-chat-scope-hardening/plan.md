# Plan
Use agent/mcp_chat.py only: a shared policy/prompt builder and validated history
serialization before provider transport. Preserve canonical tool dispatch, tenant
scope, confirmation and source data. No schema, service, tool catalog or UI change.
## Constitution Check
PASS: Source/Evidence/Reality remains lossless; proposals use existing tools;
tenant identity comes from caller; model cannot confirm; no new typed fields.
## Tests before implementation
Add provider-parametrized adversarial fake transports, real dispatch rejection for
confirmation, invalid history/no network and read-only parity. Run targeted tests
then full backend regression; lint/spec checks. Rollback is code-only.
## Review
User scope accepted; no unresolved clarification or exception. Fake providers prove
request/dispatch boundaries, not actual refusal rates. No live safety claim.
