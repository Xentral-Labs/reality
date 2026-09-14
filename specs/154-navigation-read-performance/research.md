# Research

Browser baseline: payments resource 4190 ms, click-to-response 4205 ms and click-to-frame 4270 ms; journal resource 52 ms / frame 689 ms; delivery resource 110 ms / response 114 ms / frame 1091 ms. Long-animation-frame attribution records 608 ms and 935 ms script work in the React MessagePort callback for Journal and Orders. Source inspection finds repeated reverse dictionary scans per text node in the shared localization mutation observer.

Decision: replace only reverse lookup with one lazily built first-match index. Reject skipping localization in English or caching business values, which would change restoration behavior or grow memory with tenant data. Preserve all dictionary and DOM semantics.

Payments API uses direct bounded rows but derives totals through the PAYMENTS projection, whose refresh still rebuilds all views. Journal uses direct journal_page and needs no backend change. Extract the existing payment projection builder and reuse spec 153's scoped refresh. No new architecture, dependency or external research is needed.
