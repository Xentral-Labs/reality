# Business Journey Guide

The Business Journey Guide is Reality's public, evidence-bounded answer to “Can Reality handle this business situation?”. Its canonical deployment catalog lives in `packages/reality-core/config/business_journey_catalog.yaml`; the public Docs payload is generated and must never carry `internal_evidence`.

## Product contract

- Every canonical scenario ID appears exactly once and keeps its business question.
- `supported` requires executable evidence. `partial`, `recognition_only`, `missing` and `out_of_scope` state their limitation rather than implying complete support.
- Explanations preserve Source → Evidence → Reality. A scenario status describes product coverage, never a stored document or fulfilment status.
- Website, Docs and ordinary authenticated Reality Chat use `services/business_journeys.py` for matching and status/citation conclusions.
- Public questions are read-only, ephemeral, rate-bounded and cannot contain tenant or company selectors. They never call mutating tools.
- Normal Reality Chat recognizes capability questions inside an ordinary conversation. Tenant-specific questions and actions retain the existing tenant-scoped tools and confirmation boundary.

## Public website embed

The marketing site is maintained in the private operations repository. This repository publishes `/journey-guide-widget/widget.js` with the Docs artifact. The host supplies only:

```html
<script
  src="https://docs.example.com/journey-guide-widget/widget.js"
  data-api-url="https://api.example.com"
  data-guide-url="https://docs.example.com/getting-started/business-journeys"
  data-locale="en"
  defer
></script>
```

The launcher is closed by default and opens an accessible, keyboard-dismissible side panel on desktop and bottom sheet on narrow screens. Header and composer remain fixed while only the ephemeral in-page conversation scrolls. Citation chips open the complete Guide journey in a new tab so the marketing page and conversation remain intact. Provider text is rendered through text nodes and safe paragraph/strong elements, never injected as HTML. The widget stores no conversation or identifier. The API/asset may fail without blocking, obscuring or changing the host page; the panel then opens the Guide in a new tab. Production completion requires a separate operations-repository embed review and deployed smoke test.

## Generation and maintenance

`make docs-generate` validates the catalog and writes the same public payload to the Docs component data and downloadable static JSON. Additions and status changes therefore reach browsing and question matching together. CI rejects duplicate IDs, invalid support/evidence combinations, broken related journeys and public leakage of internal evidence.

The [Demo Data Catalog](demo-data-catalog.md) remains the smaller inventory of concrete cases seeded in the current demo profile. A cataloged journey without a demo reference is not presented as immediately explorable.
