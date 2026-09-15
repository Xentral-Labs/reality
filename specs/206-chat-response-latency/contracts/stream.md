# Chat stream
POST existing `/api/tenants/{tenant}/copilot/sessions/{session}/messages?stream=true` with the unchanged message/context body and existing authentication. Content type `application/x-ndjson`; each line is one JSON event.

- `{"type":"start"}`: accepted response, not proof of completed service work.
- `{"type":"reset"}`: clear provisional current-round text.
- `{"type":"delta","text":"..."}`: append presentation text, never tool JSON.
- `{"type":"done","user":{"id":"...","content":"..."},"assistant":{"id":"...","content":"..."}}`: authoritative completed response after service persistence; replaces provisional text.
- `{"type":"error","message":"..."}`: request could not complete; no automatic resend.

A stream ending without done is incomplete. Provider failure may produce the existing durable safe failure answer via done; partial provider text is replaced. Preflight admission errors retain HTTP error behavior. JSON clients omitting stream remain unchanged. Reverse proxies must not buffer. No tool arguments or prompts in timing logs. Completion does not authorize proposals.
