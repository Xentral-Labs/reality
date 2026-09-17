# Plan
Change shared inspectorSections labels so navigation, tooltip, aria-current and area-label consumers stay coherent. Change the standalone FactsPage header and pageIntroduction entry only. Rename three StorylineProtocol graph labels; keep the Facts count group and record selectors untouched. Add Business Facts as a product-name translation and replace the Context Graph catalog/invariant entry with Business Graph.

Constitution Check: PASS for all eight principles. Presentation-only; no domain, schema, service, source, tenant or action changes. No dependencies or unresolved research questions.

Test-first: update existing navigation and vocabulary expectations and observe red; implement labels; run all frontend tests, formatting, language audit, production build and spec policy. Run existing multilingual browser suite and visually inspect navigation. No backend tests for label-only changes. Revert labels/catalog/tests together to roll back.

## Public guidance (FR-004)

Update docs home, onboarding, first-trace and glossary in English/German. Explain
product group versus typed Fact explicitly. Use existing layout and links; no new
navigation or generated-catalog changes. Provider site lives in reality-internal:
update LandingPage/WhyRealityPage labels and add three concise explanations using
existing responsive cards; translate source copy in all advertised languages.
Constitution Check: PASS; presentation only. Review: no clarifications/critical gaps.
Run docs tests/build, site tests/i18n/build and inspect both pages at mobile/desktop.
No backend or schema checks are needed. Rollback restores copy and labels.
