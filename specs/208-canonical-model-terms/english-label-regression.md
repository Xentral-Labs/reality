# English label regression — FR-003

## Specification review
Restore existing FR-003: English copy must remain unchanged. The DOM reverse lookup
mistakes Commitments for the localized value of Business commitments. This is a bug
fix, not a terminology or product-scope change. User authorized the fix.

## Plan and Constitution Check
Prefer known English source keys over reverse-translation aliases in the shared
resolver. Preserve first-match behavior for non-source translations and lazy caching.
No model, service, schema, tenant or original-content boundary changes. All principles
PASS; no exceptions. Existing frontend stack and shared resolver, no new dependencies.

## Tasks and analysis
- [x] T001: Add actual-catalog English-key and Commitments collision regressions first.
- [x] T002: Correct resolver precedence centrally.
- [x] T003: Run frontend/spec gates and four-language navigation browser checks.
FR-003 is covered by all tasks. No ambiguity or critical analysis findings.

## Verification and final review
The regression failed before the fix (Normal became Normal rows); after the fix,
all canonical source keys and Commitments remain exact. Existing translated-alias,
original-content, formatting and cache tests pass. `gmake spec-check web-build`
passed with 219 tests, localization audit and TypeScript/Vite build.
The browser confirms exact Commitments navigation in en/de/nl/es, including mobile,
legacy links and back/forward. No browser errors or writes. Reviewed the six-line
resolver change: catalog initialization remains lazy and cached, with no business
logic, authority or original-payload changes. Existing large-bundle advisory only.
