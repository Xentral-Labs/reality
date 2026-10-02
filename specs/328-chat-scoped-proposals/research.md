# Research

- `copilots_payload` used `proposals_awaiting_approval(tenant)`: every pending proposal of the company.
- `ChangeProposal` (`action`) had no chat reference. The Storyline recorder links calls only inside a storyline.
- All pending proposals are made by `create_change_proposal` (`tools/application.py`), reached from MCP propose
  tools, chat tool calls, the local provider (`propose_tool`) and service drafts (company party, cost review).
  Other direct `ChangeProposal(...)` rows are executed records, never pending.
- A chat turn is one `send_chat_message` call. Messages were added at the end of the turn, so both got the
  insert time and a proposal made during the turn was older than its own question.
- `remove_chat_session` deletes a session without messages. A turn that failed after its proposal was committed
  could leave such a session holding a proposal; the FK would block deletion, so removal archives instead.
- Decisions page (`DecisionsPage.tsx`) already lists pending and decided proposals with `DecisionLine`.
