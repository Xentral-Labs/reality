# Contract: Read Capability Description

`capability_describe({tool_name})` returns `kind: read`, public `tool_name`,
`application_tool`, purpose, use/non-use, required context, data basis, limitations,
freshness, empty/refusal behavior, verification role, `proves`, `does_not_prove`,
`unknown_when`, next steps, and positive/negative examples.

The call is read-only. Unknown/internal tools are not found. Existing proposal response
shape remains compatible.

