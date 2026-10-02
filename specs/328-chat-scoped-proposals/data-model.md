# Data Model

`action` (ChangeProposal) gains `chat_session_id varchar NULL`, FK `(tenant_id, chat_session_id)` →
`chat_session(tenant_id, id)`, index `ix_action_tenant_chat_session (tenant_id, chat_session_id)`.
Set once at creation inside a chat turn; null otherwise and for every existing row. Derived at read time, not stored:
`after_message_id`, `pending_elsewhere`.
