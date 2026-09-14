# Implementation Plan: Exception Rules Register

**Language**: English

## Constitution Check

- Nothing is stored: the per-class count and the class filter run the existing operational
  exception derivation at read time; no schema change, no new authority.
- Web calls the shared service (`attention_reads`) through the tenant API; no second business
  rule in the browser.
- Every read is tenant-scoped through `get_tenant`; an unknown class id is refused with 422.

## Steps

1. Service: add `class_id` to `attention_register` and a new `attention_summary` that counts
   the derived rows per catalog class, listing every class in catalog order.
2. API: `class_id` query parameter on `GET /api/tenants/{tenant}/attention`; new
   `GET /api/tenants/{tenant}/attention/summary`, declared before the identity route.
3. Tests first: service tests for the filter, the refusal and the summary (including a count
   dropping after a reservation); HTTP boundary assertions in the unified operations test.
4. Web: `ExceptionRulesRegister` renders the catalog as a `RegisterTable` with an inline
   `TablePreview`; the Inspector's exceptions tab uses it; the Exception catalog dialog keeps
   the disclosure list. Client helpers `operationsApi.attentionSummary` and the class filter.
5. Localization for de, nl, es; i18n audit.
6. Browser: extend `unified-inspector-browser.mjs` fixtures and assertions; verify with a
   focused run at 1440px and 390px in English and German.
7. Labels: `load_exception_class_labels` reads `labels.<language>.exceptions` from the resource
   catalog; the exception catalog read returns them per class; the web picks the UI language
   and falls back to the catalog label.
