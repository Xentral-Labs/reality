# Research

- Decision: stream existing APIs with httpx. Anthropic block indexes and partial JSON must be assembled before dispatch; require message_stop. OpenAI-compatible chunks need indexed tool-call assembly and [DONE]. Rationale: reuse provider and confirmation path. Alternative full SDK adds unnecessary dependency.
- Decision: retain all schemas and mark stable Anthropic tools/system prefixes with ephemeral cache control, built once per invocation. Preserve text-only system prompt semantics. Alternative native deferred tool search changes model selection and adds server-tool blocks/rounds; defer until measured.
- Decision: compact JSON without dropping fields; no separate agent business projection.
- Decision: request-scoped event callback/worker bridge rather than durable scheduling or duplicated async business service. Worker owns DB session; no replay on disconnect.
- Decision: batch current inventory reads using canonical revision/fulfillment terms, not a cached stock authority. No new index based on the sub-millisecond local plans.

Official references checked on 2026-09-15:
- https://platform.claude.com/docs/en/build-with-claude/streaming
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://developers.openai.com/api/reference/resources/chat
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool

Baseline: four requests 8.088–12.647 s, 98.65% provider time; tools 67–224 ms; 130 SQL statements/tool; 34k initial input tokens; zero cache-read tokens. The old local deployment predates latest main; compare cautiously and retain raw measurement conditions.
