# Data Model
No schema change. Existing StorylineTraceEntry chat.reply association stores
input.message_id and result.trace_ids. The IDs reference existing assistant messages
and trace entries. Existing proposal_id links subsequent decisions. Association
retention is the existing run ring; missing entries are reported, never reconstructed.

Independent Free Play also reuses the company-setup PlaygroundRun receipt with the
owner-scoped immutable request key `standalone-free-play:v1`. It is practice kind,
canonical demo profile, and null storyline_key/version. It needs no extra marker,
new business field or migration. An ordinary-company receipt is refused.
