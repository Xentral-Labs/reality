# Data Model
No schema change. Existing StorylineTraceEntry chat.reply association stores
input.message_id and result.trace_ids. The IDs reference existing assistant messages
and trace entries. Existing proposal_id links subsequent decisions. Association
retention is the existing run ring; missing entries are reported, never reconstructed.
