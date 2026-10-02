# Data Model

No database changes. A transient immutable ProposalDecisionPolicy represents action
approval authority, required enforcement checks and existing contextual exceptions.
It derives from registered action identity and stored proposal arguments. Rejection
is separately access-context governed. Explicit decision is required; permitted
paths are authenticated Web, permissioned external MCP and existing local CLI.
Built-in Chat cannot settle. Autonomous delegation and verified human involvement
are false. These values neither persist as authority nor alter attribution.
