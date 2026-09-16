# Plan
Change shared inspectorSections labels so navigation, tooltip, aria-current and area-label consumers stay coherent. Change the standalone FactsPage header and pageIntroduction entry only. Rename three StorylineProtocol graph labels; keep the Facts count group and record selectors untouched. Add Business Facts as a product-name translation and replace the Context Graph catalog/invariant entry with Business Graph.

Constitution Check: PASS for all eight principles. Presentation-only; no domain, schema, service, source, tenant or action changes. No dependencies or unresolved research questions.

Test-first: update existing navigation and vocabulary expectations and observe red; implement labels; run all frontend tests, formatting, language audit, production build and spec policy. Run existing multilingual browser suite and visually inspect navigation. No backend tests for label-only changes. Revert labels/catalog/tests together to roll back.
