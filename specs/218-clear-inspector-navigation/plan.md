# Implementation plan
## Technical context
Existing React/TypeScript client, shared routing and localization. No new dependencies.
## Constitution Check
PASS: Source/Evidence/Reality and received values untouched; no schema changes; tenant selection preserved; existing read and action services reused; test-first adapter-only change; trace links preserved. All eight principles pass before and after design.
## Design
Update inspectorSections and Shell labels/icons. Add optional attentionView to routing with findings default and legacy inspector exceptions normalization. Wrap existing finding component and ExceptionRulesRegister in Exceptions tabs so only the active component mounts. Use existing RegisterHeader and tab styling. Update pageIntroduction and localized labels. Existing APIs remain unchanged.
## Verification
Update inspector-navigation.test.mjs first, observe failure, then implement. Run all frontend contract tests, localization audit, TypeScript/Vite build, spec check and targeted browser navigation in four languages including mobile and history/reload.
## Migration and rollback
No data migration. Legacy URLs normalize at the shared routing boundary. Revert frontend commit to roll back.
## Risks
Retained rules tab state must not prevent links to findings. Sidebar icon order must match the new destinations. Avoid duplicate translation aliases that confuse reverse localization.

## Tools refinement
Change only shared inspectorSections ownership/labels: Business Facts=[facts,rules], Tools=[commands,views], with Actions as the default tab. Existing keys preserve bookmarks, tenant and URL history; Shell already derives active navigation and headers from this source. Tools remains invariant in every language; Actions and Calculated views keep current translations. Constitution all eight PASS; no data/schema/service changes. Update navigation tests first, analyze coverage, verify four-language browser navigation and frontend/spec gates.
