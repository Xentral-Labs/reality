# Agent
Provider-neutral chat orchestration. Reads can execute; mutations require confirmation. Use the same tools/services as CLI. Include a deterministic dummy provider for tests.

The shared provider prompt limits assistance to Reality product usage and supported
business workflows. User/history/source/tool content is evidence, never authority
to change scope, reveal credentials or approve actions. Both adapters validate that
history contains only textual user/assistant turns, and both use the same read-only
companion policy. Provider dispatch retains the caller tenant and the read/propose
allowlist; confirmation cannot be delegated to model output.

The scope prompt is a probabilistic behavioral control, not an authorization
boundary or a guarantee against prompt injection. `tests/test_chat_scope_security.py`
uses adversarial fake provider responses to verify transport and tool boundaries;
it does not establish a live-model refusal rate. See spec 197 for evaluation evidence.
