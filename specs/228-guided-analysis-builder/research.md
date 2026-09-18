# Research

## Decisions
- Reuse Traversal and graph.ask. Alternatives (browser SQL, Neo4j, arbitrary Cypher) break the existing checked measure/tenant boundary.
- Generate parameterized path text in the shared service and test parsing it back. Extend missing alias/NOT IN support so text cannot silently drop grouping meaning. Preserve advanced HAVING/EXISTS/recursion in expert mode.
- Free-text interpretation is one constrained provider call with a typed result, not conversational prose parsing or a save proposal. Reuse configured provider secrets, tenant policy and managed question reservation. Validate the proposed Traversal before returning.
- Use executable templates for examples. Open balance currently refuses service-bound graph measures; no invoice aging or product-group revenue evidence exists. Never relabel order value as revenue.
- Summary cards expose actual result metadata rather than inventing full-query totals from capped rows. Node counts are unavailable; show actual path and multiplicity without false counts.
- Reference hosting requires authentication; supplied screenshots remain the visual source. No active computer browser was available during initial inspection.

Research included an independent read-only audit of model, provider, graph tool and persistence contracts. No new infrastructure or dependencies are required.

## Design refinement review
Owner explicitly removes the pictured Builder heading/status and question/examples panel while preserving the functional structure. Designer review identifies spec225 flat register styling as the current authority. Shared semantic tokens preserve meaningful sentence colors and automatically support themes. Analysis: no critical conflicts after superseding FR-001/002/010 screenshot presentation; backend interpretation remains available.

## Shared component analysis
Owner accepted the concrete seven-point comparison with operational registers. Shared components exist and require no new design system. Header portals need explicit active-view gating because Builder stays mounted under hidden content. No unresolved clarifications or critical findings; test this boundary.

## Chat integration review
Existing ChatPage handles the shared open-chat event and graph report proposals already use confirmation-protected graph.reports.change. The proposal preview endpoint validates tenant and original author and exposes the checked question. No new execution path is needed. Risks are stale composer context, cross-company reuse, unexecuted expert drafts and accidental save on template adoption; the implementation/test tasks cover these. No unresolved product clarification or critical design finding.

## Question hierarchy review
Owner identifies insufficient grouping after flat-register integration and approves a contained question area. This is an intentional local exception to flat register surfaces, not a change to workspace chrome or result tables. Period deduplication must not hide unrelated date conditions, and hiding advanced controls must not alter the query. No unresolved clarification or critical findings.
