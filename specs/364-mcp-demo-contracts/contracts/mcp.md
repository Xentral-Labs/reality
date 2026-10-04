# MCP Contract

`tools/list.inputSchema` preserves the registered schema, including enums and nested
constraints. Typed handlers and canonical validation remain in force.

`proposal_review.confirmation` names the tool, complete arguments and explicit human
approval requirement. Retained proposals include their fingerprint. Older generic
eligible proposals explicitly require preparation followed by a new review and decision;
a preparation response must never be reported as execution.

Execution and reconciliation responses provide current callable verification guidance
beside the original receipt. Recorded `receipt.verification_reads` remains unchanged;
its internal projection basis is not an API tool name.
