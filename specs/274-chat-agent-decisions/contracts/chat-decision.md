# Contract: Chat Decision Lifecycle

Ordinary Chat receives `read`, `propose` and `confirm`; read-only Playground receives `read`. Conversation content cannot broaden those classes.

Prepare uses an existing typed proposal schema and returns an opaque proposal ID, exact input and preview without business effect.

Approval calls the existing tool with the exact ID, `approved=true` and a current review token when required. Rejection calls the existing rejection tool. Success returns final status and receipt; refusal returns the actual lifecycle or authority reason.

Generic Chat confirmation is an agent decision, not evidence of personal approval. Protected tools may still require a signed-in person, owner or current review.

Decision reads expose `decider.kind = chat_agent`, distinct from `person`, `mcp_token` and `unknown`.

Invariants: proposal creation never executes; foreign/unknown proposals cannot be settled; settlement is single-use; untrusted content cannot grant authority; provider adapters behave identically.
