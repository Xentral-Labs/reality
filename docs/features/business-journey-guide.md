# Business Journey Guide

The Business Journey Guide is Reality's public, evidence-bounded answer to “Can Reality handle this business situation?”. The Reality Product Advisor researches this catalog together with reviewed public product contracts and the executable tool vocabulary. Its canonical deployment catalog lives in `packages/reality-core/config/business_journey_catalog.yaml`; public payloads are generated and must never carry `internal_evidence`.

## Product contract

- Every canonical scenario ID appears exactly once and keeps its business question.
- `supported` requires executable evidence. `partial`, `recognition_only`, `missing` and `out_of_scope` state their limitation rather than implying complete support.
- Explanations preserve Source → Evidence → Reality. A scenario status describes product coverage, never a stored document or fulfilment status.
- Website, Docs, the canonical read tool and ordinary authenticated Reality Chat use `services/product_advisor.py` for the same researched claims, support ceilings and citations.
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

The launcher is closed by default and opens an accessible, keyboard-dismissible side panel on desktop and bottom sheet on narrow screens. Header and composer remain fixed while only the ephemeral in-page conversation scrolls. Conversation body type and answer spacing use a compact reading density so a structured response exposes more useful content without sacrificing legibility; user messages remain distinct through placement, color and shape rather than oversized type. Citation chips open the complete Guide journey in a new tab so the marketing page and conversation remain intact. Provider text is rendered through text nodes and safe paragraph/strong elements, never injected as HTML. The widget stores no conversation or identifier. The API/asset may fail without blocking, obscuring or changing the host page; the panel then opens the Guide in a new tab. Production completion requires a separate operations-repository embed review and deployed smoke test.

## Generation and maintenance

`make docs-generate` validates the Journey catalog, regenerates its browsing payload and builds `product_advisor_knowledge.json`. Additions and status changes therefore reach browsing and advisor research together. `make docs-catalog-check` fails when either generated artifact is stale.

`product_advisor_sources.yaml` is the reviewed allowlist for durable public documents. A source is eligible only when it is public-safe, has a stable public URL and is assigned an explicit authority: capability evidence, executable vocabulary, technical contract or explanation. Specifications, plans, tasks, tests, private paths and tenant data are not Advisor sources. The product/domain owner reviews capability sources; the owning engineering reviewer approves technical contracts and executable vocabulary.

Each generated source and evidence unit has a content fingerprint, stable ID and one immutable knowledge version. Generation rejects missing documents, duplicate IDs, broken source references and unsafe public locations. The release check regenerates the artifact and compares it with the checked-in output, so changing an allowlisted source without committing the new artifact is a build failure.

The public Advisor may explain native behavior, a manual step, a confirmation-bound agent proposal, a workaround or a genuine gap. It may never promote limited evidence to proven support, present executable vocabulary as proof that an end-to-end process exists, or omit a material limitation. Provider failure falls back to the same bounded evidence and never expands the conclusion.

When the latest question can refer to materially different ERP flows, the Advisor asks one focused clarification before research instead of letting conversation history silently choose a flow. In particular, an unqualified “partial delivery” question distinguishes a customer shipment from a partial supplier goods receipt. Once the trading side is explicit, retrieval uses side-specific vocabulary. Public Journey summaries used as deterministic fallback state a concrete business outcome and must not merely repeat their title or question.

Authorized internal calls receive the same public conclusion and may additionally receive allowlisted internal evidence for cited Journey IDs. This diagnostic material is returned separately, remains tenant-independent and is never serialized by the public API or widget. Remediation starts by fixing the canonical source or allowlist, regenerating the artifact and rerunning the claim and buyer-case evaluations; generated JSON is not edited by hand.

The [Demo Data Catalog](demo-data-catalog.md) remains the smaller inventory of concrete cases seeded in the current demo profile. A cataloged journey without a demo reference is not presented as immediately explorable.
