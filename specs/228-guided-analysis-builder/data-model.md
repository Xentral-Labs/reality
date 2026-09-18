# Data model

No persistence changes. Existing Traversal retains every hop, origin, depth, filter, group alias, measure, HAVING, EXISTS, ordering and limit. Analysis draft holds question text, selected tab/node, canonical question, path/parameters and unexecuted-draft state. A monotonic request generation prevents stale async responses. Switching company remounts the workspace.

Existing analytics_report remains owner/tenant scoped and stores only the validated question. An editor draft must execute successfully before it can become a saved question. Unsupported simple forms remain expert-only; returning to the builder is an explicit reset.
