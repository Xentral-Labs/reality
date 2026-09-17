# Verification

2026-09-16. Approved scope and related-label boundary reviewed; three requirements mapped to three tasks. No clarifications, critical findings or Constitution exceptions.

- Existing Inspector navigation and model vocabulary tests observed red with old names, then passed with Business Graph/Business Facts. Legacy routes, tab destinations and query filters remain covered.
- `gmake spec-check web-build`: passed, including formatting, 211 frontend tests, all four language audits, TypeScript and production build. Existing bundle-size advisory only.
- Existing operational browser suite passed in en/de/nl/es at desktop/mobile widths, covering keyboard disclosure and full-detail actions. German desktop screenshot visually reviewed: both new names fit in the sidebar with their existing icons. Local artifacts: `/private/tmp/reality-209-browser/`.
- Caller review: inspectorSections supplies navigation/tooltips; FactsPage and pageIntroduction supply standalone headings; StorylineProtocol has three graph references renamed. No remaining Context Graph UI references. ContextExplorer/InspectorRecordsPage Fact type filters and Storyline Facts count remain unchanged. Shell continues to title sub-tabs descriptively rather than replacing Timeline or All records.
- No backend tests required for label-only changes. Technical identifiers, business values, routes and APIs are unchanged.

## Public Inspector explanations (FR-004, 2026-09-17)

Docs home, onboarding, first-trace and glossary now map Business Graph, Business
Facts and Tools to the UI in English/German. The Fact datatype remains distinct;
Event history remains a separate event log. Generated catalogs and technical
identifiers were not changed. Provider landing/explanation changes are in the
separate reality-internal repository, spec022 FR-029, with four-language copy.

Verification: 67 docs tests, VitePress production build, changed-page formatting,
spec policy and diff checks passed. Provider: 77 tests, four-language audit and
production build passed. Browser reviewed the landing/explanation in en/de/nl/es
and all eight edited docs pages at 390/1440px: no page overflow or browser errors.
Visual review replaced a cramped docs-home table with plain explanations and
corrected the landing cards' text contrast on their dark background. Product labels
are stable; old public Context Graph wording is gone. No publication, commit or
backend/schema change. User-approved scope, Constitution PASS, no critical findings.

PR branch verification on current main (e8cc4469): 68 documentation tests and the
VitePress production build passed; spec policy and diff checks passed. The provider
PR preserves its newer main-branch hero and ProductStory, places the three cards in
the existing product section, and renames ProductStory's graph label as well.
